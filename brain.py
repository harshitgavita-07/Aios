from llm import ask_llm

def brain(user_input: str) -> str:
    try:
        text = user_input.strip()
        if not text:
            return "Please type something."

        return ask_llm(text)

    except Exception as e:
        return f"Brain Error: {str(e)}"