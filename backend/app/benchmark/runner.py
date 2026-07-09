import json
import os
import time
from sqlalchemy.orm import Session
from app.database.models import BenchmarkModel
from app.providers.local_ollama import LocalOllamaProvider
from app.providers.remote_fireworks import RemoteFireworksProvider
from app.router.routing_engine import RoutingEngine
from app.evaluation.consistency import ConsistencyChecker
from app.evaluation.hallucination import HallucinationDetector
from app.config import settings

class BenchmarkRunner:
    def __init__(self, db: Session):
        self.db = db
        self.ollama = LocalOllamaProvider()
        self.fireworks = RemoteFireworksProvider()
        self.router = RoutingEngine()
        self.consistency = ConsistencyChecker(self.ollama)
        self.hallucination = HallucinationDetector()

    def _load_tasks(self) -> list:
        # Look for sample_tasks.json in parents
        possible_paths = [
            "sample_tasks.json",
            "../sample_tasks.json",
            "../../sample_tasks.json",
            os.path.join(os.path.dirname(__file__), "..", "..", "sample_tasks.json")
        ]
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, "r") as f:
                    return json.load(f)

        # Fallback tasks if file cannot be found
        return [
            {"id": 1, "type": "factual", "task": "What is the capital of Japan?", "expected": ["tokyo"]},
            {"id": 2, "type": "factual", "task": "Who painted the Mona Lisa?", "expected": ["da vinci", "leonardo"]},
            {"id": 3, "type": "math", "task": "What is the result of 15 * 6?", "expected": ["90"]},
            {"id": 4, "type": "code", "task": "Write a python function called 'add_two' that takes two parameters and returns their sum.", "expected": ["def add_two", "return"]},
            {"id": 5, "type": "summarization", "task": "Summarize in one word the topic of computers: they store data and compute information.", "expected": ["computer", "technology", "computation"]}
        ]

    def _check_accuracy(self, response_text: str, expected_keywords: list) -> bool:
        resp_lower = response_text.lower()
        return all(keyword.lower() in resp_lower for keyword in expected_keywords)

    def run_benchmark(self, benchmark_name: str, threshold: float = 0.8) -> dict:
        tasks = self._load_tasks()
        total_tasks = len(tasks)

        configs = ["always_local", "always_remote", "triforge_router"]
        runs_summary = {}

        # Estimated cost rate
        remote_token_rate = 0.20 / 1_000_000

        for mode in configs:
            passed = 0
            total_latency = 0.0
            remote_tokens_spent = 0
            local_tokens_spent = 0

            for task in tasks:
                start_time = time.time()
                prompt = task["task"]
                expected = task["expected"]

                ans = ""
                p_tok, c_tok = 0, 0

                if mode == "always_local":
                    ans, p_tok, c_tok = self.ollama.generate(prompt, settings.ACTIVE_LOCAL_MODEL)
                    local_tokens_spent += (p_tok + c_tok)

                elif mode == "always_remote":
                    ans, p_tok, c_tok = self.fireworks.generate(prompt, settings.ACTIVE_REMOTE_MODEL)
                    remote_tokens_spent += (p_tok + c_tok)

                elif mode == "triforge_router":
                    # Full TriForge routing run
                    route_name, reason, estimates = self.router.route(prompt)
                    if route_name == "local":
                        # consistency check
                        sim, s1, s2, s_p, s_c = self.consistency.check_consistency(prompt, threshold=threshold)
                        local_tokens_spent += (s_p + s_c)

                        flagged_info = self.hallucination.check_hallucination_signals(s1)
                        
                        if sim < threshold or flagged_info["flagged"]:
                            # escalate
                            ans, r_p, r_c = self.fireworks.verify_draft(prompt, s1, settings.ACTIVE_REMOTE_MODEL)
                            remote_tokens_spent += (r_p + r_c)
                        else:
                            ans = s1
                    else:
                        ans, r_p, r_c = self.fireworks.generate(prompt, settings.ACTIVE_REMOTE_MODEL)
                        remote_tokens_spent += (r_p + r_c)

                latency = (time.time() - start_time) * 1000
                total_latency += latency

                # Check accuracy
                if self._check_accuracy(ans, expected):
                    passed += 1

            accuracy = (passed / total_tasks) * 100 if total_tasks > 0 else 0.0
            avg_latency = total_latency / total_tasks if total_tasks > 0 else 0.0
            estimated_cost = remote_tokens_spent * remote_token_rate

            runs_summary[mode] = {
                "accuracy": round(accuracy, 2),
                "latency_avg_ms": round(avg_latency, 2),
                "remote_tokens": remote_tokens_spent,
                "local_tokens": local_tokens_spent,
                "cost_usd": round(estimated_cost, 6)
            }

        # Calculate routing savings relative to "always_remote"
        remote_cost = runs_summary["always_remote"]["cost_usd"]
        router_cost = runs_summary["triforge_router"]["cost_usd"]
        savings = max(0.0, remote_cost - router_cost)

        # Log router benchmark result to DB
        router_stats = runs_summary["triforge_router"]
        benchmark_entry = BenchmarkModel(
            benchmark_name=benchmark_name,
            total_tasks=total_tasks,
            accuracy=router_stats["accuracy"],
            remote_tokens=router_stats["remote_tokens"],
            local_tokens=router_stats["local_tokens"],
            cost=router_stats["cost_usd"],
            savings=round(savings, 6),
            latency_avg=router_stats["latency_avg_ms"],
            config_json=json.dumps(runs_summary)
        )

        self.db.add(benchmark_entry)
        self.db.commit()
        self.db.refresh(benchmark_entry)

        return {
            "id": benchmark_entry.id,
            "benchmark_name": benchmark_name,
            "timestamp": benchmark_entry.timestamp.isoformat(),
            "total_tasks": total_tasks,
            "results": runs_summary,
            "savings_usd": round(savings, 6)
        }
