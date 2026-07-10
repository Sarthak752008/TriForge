"""
Quick test to verify routing decisions for all 10 eval tasks.
Run: python test_routing.py
Expected: tasks 1-4, 6-10 → LOCAL (0 Fireworks tokens)
          task 5           → remote_tier1 (code generation)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from router import route, _classify

tasks = [
    {"id": 1,  "type": "factual",       "task": "What is the capital of Japan?"},
    {"id": 2,  "type": "factual",       "task": "Who painted the Mona Lisa?"},
    {"id": 3,  "type": "math",          "task": "What is the result of 15 * 6?"},
    {"id": 4,  "type": "math",          "task": "What is 257 * 149 - 28?"},
    {"id": 5,  "type": "code",          "task": "Write a python function called 'add_two' that takes two parameters and returns their sum."},
    {"id": 6,  "type": "code_qa",       "task": "What standard python keyword is used to handle exceptions?"},
    {"id": 7,  "type": "summarization", "task": "Provide a 1-sentence summary of the following story: Once upon a time, a young boy named Leo found a golden key in the forest. He searched for days to find what it opened, only to discover it unlocked a chest containing old books of wisdom. Leo spent the rest of his life reading them and became the wisest man in his village."},
    {"id": 8,  "type": "factual",       "task": "Which planet is known as the Red Planet?"},
    {"id": 9,  "type": "math",          "task": "Solve the algebraic equation: 3x + 7 = 22. What is the value of x?"},
    {"id": 10, "type": "summarization", "task": "Summarize the primary purpose of local LLMs like Ollama in 10 words or less."},
]

EXPECTED = {
    1:  "local",
    2:  "local",
    3:  "local",
    4:  "local",
    5:  "remote_tier1",   # Code generation — needs Fireworks
    6:  "local",
    7:  "local",
    8:  "local",
    9:  "local",
    10: "local",
}

print("\n" + "=" * 70)
print("  TriForge Router Verification — All 10 Eval Tasks")
print("=" * 70)
print(f"  {'ID':<4} {'Type':<14} {'Category':<15} {'Route':<16} {'Status'}")
print("-" * 70)

all_pass = True
local_count = 0

for t in tasks:
    cat   = _classify(t["task"])
    route_name, reason = route(t["task"])
    expected = EXPECTED[t["id"]]
    status   = "PASS" if route_name == expected else f"FAIL (expected {expected})"
    if route_name != expected:
        all_pass = False
    if route_name == "local":
        local_count += 1
    print(f"  {t['id']:<4} {t['type']:<14} {cat:<15} {route_name:<16} {status}")

print("=" * 70)
fireworks_tasks = len(tasks) - local_count
print(f"\n  LOCAL  (0 Fireworks tokens): {local_count}/{len(tasks)} tasks")
print(f"  REMOTE (Fireworks billed)  : {fireworks_tasks}/{len(tasks)} tasks")
print(f"\n  Estimated Fireworks token savings: ~{fireworks_tasks * 400} tokens avoided")
print(f"\n  Overall: {'ALL PASS' if all_pass else 'SOME FAILURES -- check router.py'}")
print()
