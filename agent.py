import os
import sys
import requests
import difflib
from router import route

# Simple helper to load environment variables from .env
def load_env():
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")

# Call the local Ollama model with a configurable temperature
def call_local(prompt: str, temperature: float = 0.7) -> tuple[str, int, int]:
    """
    Calls the local model using Ollama with a custom temperature.
    Returns:
        tuple: (response_text, prompt_tokens, completion_tokens)
    """
    url = "http://localhost:11434/api/chat"
    model = "qwen2.5:3b-instruct"
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        content = data.get("message", {}).get("content", "")
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)
        return content, prompt_tokens, completion_tokens
    except Exception as e:
        return f"Error querying local model: {e}", 0, 0

# Call the remote Fireworks model
def call_remote(prompt: str) -> tuple[str, int, int]:
    """
    Calls the remote Fireworks AI model.
    Returns:
        tuple: (response_text, prompt_tokens, completion_tokens)
    """
    load_env()
    api_key = os.environ.get("FIREWORKS_API_KEY")
    if not api_key:
        return "Error: FIREWORKS_API_KEY is not set.", 0, 0
        
    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    model = "accounts/fireworks/models/llama-v3p1-8b-instruct"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        return content, prompt_tokens, completion_tokens
    except Exception as e:
        return f"Error querying remote model: {e}", 0, 0

# Call the remote Fireworks model with a draft for verification/correction
def call_remote_verify(prompt: str, draft: str) -> tuple[str, int, int]:
    """
    Sends the original task and the local draft to Fireworks, asking it to verify or correct.
    This saves completion tokens since the remote model doesn't need to rebuild the answer from scratch.
    """
    verification_prompt = (
        f"You are an expert verifier. Review the draft answer for the given task.\n"
        f"If the draft is correct and complete, confirm it. If it is incorrect, incomplete, "
        f"or has errors, correct it.\n\n"
        f"Task: {prompt}\n"
        f"Draft Answer: {draft}\n\n"
        f"Response (be concise, verify/correct the draft):"
    )
    return call_remote(verification_prompt)

def run_agent(task_text: str, consistency_threshold: float = 0.8, silent: bool = False) -> dict:
    if not silent:
        print(f"\nTask: {task_text}")
        print("-" * 50)
    
    # 1. Ask the router where to send the task initially
    selected_route, reason = route(task_text)
    if not silent:
        print(f"Routing Decision: {selected_route.upper()}")
        print(f"Reason: {reason}")
        print("-" * 50)
    
    remote_spent = 0
    local_spent = 0
    local_saved = 0
    escalated = False
    
    # 2. Call the chosen model path
    if selected_route == "local":
        if not silent:
            print("Running local self-consistency check (sampling twice with temperature=0.7)...")
        # Sample 1
        sample1, s1_p, s1_c = call_local(task_text, temperature=0.7)
        local_spent += (s1_p + s1_c)
        
        # Sample 2
        sample2, s2_p, s2_c = call_local(task_text, temperature=0.7)
        local_spent += (s2_p + s2_c)
        
        # Compute string similarity
        similarity = difflib.SequenceMatcher(None, sample1, sample2).ratio()
        if not silent:
            print(f"Sample 1: {sample1.strip()[:100]}...")
            print(f"Sample 2: {sample2.strip()[:100]}...")
            print(f"Agreement Similarity: {similarity:.2f} (Threshold: {consistency_threshold})")
        
        if similarity >= consistency_threshold:
            if not silent:
                print("Agreement is HIGH. Checking for hedging in local model output...")
            
            # Common phrases suggesting the local model is uncertain or unable to answer
            hedging_phrases = [
                "i'm not sure", "i am not sure", "not sure if", "might be", "could be",
                "i don't know", "i do not know", "cannot answer", "unable to answer",
                "i apologize", "as an ai", "cannot verify"
            ]
            
            sample1_lower = sample1.lower()
            detected_hedges = [phrase for phrase in hedging_phrases if phrase in sample1_lower]
            
            if detected_hedges:
                if not silent:
                    print(f"Hedging detected (found: '{detected_hedges[0]}'). Escalating via verify-draft...")
                escalated = True
                answer, r_p, r_c = call_remote_verify(task_text, sample1)
                remote_spent = r_p + r_c
                local_saved = 0
            else:
                if not silent:
                    print("No hedging detected. Trusting local model output.")
                answer = sample1
                local_saved = s1_p + s1_c  # The prompt + completion tokens we successfully resolved locally
        else:
            if not silent:
                print("Agreement is LOW. Escalating via verify-draft...")
            escalated = True
            # We send sample1 as the draft since it's a candidate answer
            answer, r_p, r_c = call_remote_verify(task_text, sample1)
            remote_spent = r_p + r_c
    else:
        answer, r_p, r_c = call_remote(task_text)
        remote_spent = r_p + r_c
        
    final_route = "LOCAL -> ESCALATED TO REMOTE" if escalated else selected_route.upper()
    
    # 3. Print results and token consumption details
    if not silent:
        print("-" * 50)
        print("Answer:")
        print(answer)
        print("-" * 50)
        print(f"Final Route Taken: {final_route}")
        print(f"Remote Tokens Spent: {remote_spent}")
        print(f"Local Tokens Spent:  {local_spent}")
        print(f"Local Tokens Saved:  {local_saved} (Zero Cost)")
        print("=" * 50)
        
    return {
        "answer": answer,
        "remote_spent": remote_spent,
        "local_spent": local_spent,
        "local_saved": local_saved,
        "route": final_route
    }


if __name__ == "__main__":
    # Allow passing task as a command line argument, e.g. python agent.py "Hello"
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        run_agent(task)
    else:
        # Fallback to interactive prompt if no args provided
        print("Please enter a task (or type 'exit' to quit):")
        while True:
            try:
                task = input("\nPrompt: ").strip()
                if not task:
                    continue
                if task.lower() in ["exit", "quit"]:
                    break
                run_agent(task)
            except KeyboardInterrupt:
                break
