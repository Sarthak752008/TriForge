# router.py

def route(task_text: str) -> tuple[str, str]:
    """
    Dumbest possible rule-based routing function.
    Decides whether to route the task to 'local' or 'remote' model.
    
    Returns:
        tuple[str, str]: (route_name, reason) where route_name is 'local' or 'remote'
    """
    task_lower = task_text.lower()
    
    # 1. Length-based routing: Longer prompts usually represent complex descriptions,
    # context-heavy summaries, or coding tasks which a local 3B model might struggle with.
    word_count = len(task_text.split())
    if word_count > 25:
        reason = f"Prompt is relatively long ({word_count} words). Routed to remote model for better long-context comprehension."
        return "remote", reason
        
    # 2. Keyword-based routing: Certain tasks are notoriously difficult for smaller models.
    # Code generation/debugging and complex logical/mathematical reasoning are routed to the stronger remote model.
    complex_keywords = [
        "code", "program", "function", "class", "algorithm", "regex", "python", "javascript", # Coding
        "solve", "equation", "calculate", "prove", "math",                                   # Mathematics
        "summarize", "synthesis", "extract details"                                          # Heavy extraction/synthesis
    ]
    
    for kw in complex_keywords:
        if kw in task_lower:
            reason = f"Found complex keyword '{kw}' in prompt. Escalating to remote model for high reasoning capabilities."
            return "remote", reason

    # 3. Default fallback: Simple, short questions are routed to the local model.
    # This keeps token costs at zero for lightweight queries.
    reason = f"Prompt is short ({word_count} words) and lacks complex keywords. Routing to local model to save tokens."
    return "local", reason
