import json
import sys
from agent import run_agent

def load_tasks(filepath="sample_tasks.json"):
    with open(filepath, "r") as f:
        return json.load(f)

def run_eval(tasks, threshold=0.8, silent=False):
    total_tasks = len(tasks)
    passed = 0
    total_remote = 0
    total_local = 0
    total_saved = 0
    routes_taken = {}

    results = []
    for task in tasks:
        # Run the agent in silent mode to avoid cluttering stdout during eval
        res = run_agent(task["task"], consistency_threshold=threshold, silent=True)
        
        # Check correctness
        answer_lower = res["answer"].lower()
        is_correct = all(keyword.lower() in answer_lower for keyword in task["expected"])
        
        if is_correct:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"
            
        total_remote += res["remote_spent"]
        total_local += res["local_spent"]
        total_saved += res["local_saved"]
        routes_taken[res["route"]] = routes_taken.get(res["route"], 0) + 1
        
        results.append({
            "id": task["id"],
            "type": task["type"],
            "task": task["task"],
            "route": res["route"],
            "status": status,
            "remote_tokens": res["remote_spent"],
            "local_tokens": res["local_spent"]
        })
        
        if not silent:
            print(f"Task {task['id']} [{task['type'].upper()}]: Route={res['route']} | Status={status} | Remote Tokens={res['remote_spent']}")
            
    accuracy = (passed / total_tasks) * 100 if total_tasks > 0 else 0.0
    return {
        "accuracy": accuracy,
        "passed": passed,
        "total": total_tasks,
        "remote_spent": total_remote,
        "local_spent": total_local,
        "local_saved": total_saved,
        "routes": routes_taken,
        "details": results
    }

def main():
    tasks = load_tasks()
    
    # Check if --sweep flag is provided
    if "--sweep" in sys.argv:
        print("Sweeping confidence thresholds on evaluation dataset...")
        print("This may take a moment as it calls models multiple times.\n")
        
        thresholds = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        
        # Print table header
        print(f"| {'Threshold':<9} | {'Accuracy':<8} | {'Remote Tokens':<13} | {'Local Tokens':<12} | {'Local Saved':<11} |")
        print(f"|{'-'*11}|{'-'*10}|{'-'*15}|{'-'*14}|{'-'*13}|")
        
        for t in thresholds:
            metrics = run_eval(tasks, threshold=t, silent=True)
            acc_str = f"{metrics['accuracy']:.1f}%"
            print(f"| {t:<9.1f} | {acc_str:<8} | {metrics['remote_spent']:<13} | {metrics['local_spent']:<12} | {metrics['local_saved']:<11} |")
            
        print("\nNote: Higher thresholds trigger more escalations to remote model, raising accuracy but increasing token cost.")
    else:
        # Default single run evaluation
        threshold = 0.8
        print(f"Running evaluation with confidence threshold = {threshold}...\n")
        
        metrics = run_eval(tasks, threshold=threshold, silent=False)
        
        print("\n================ EVALUATION SUMMARY ================")
        print(f"Total Tasks:        {metrics['total']}")
        print(f"Passed Tasks:       {metrics['passed']}")
        print(f"Overall Accuracy:   {metrics['accuracy']:.1f}%")
        print(f"Total Remote Tokens: {metrics['remote_spent']}")
        print(f"Total Local Tokens:  {metrics['local_spent']}")
        print(f"Total Saved Tokens:  {metrics['local_saved']} (Zero Cost)")
        print("-" * 50)
        print("Routes Taken:")
        for r, count in metrics["routes"].items():
            print(f"  - {r}: {count} times")
        print("====================================================")

if __name__ == "__main__":
    main()
