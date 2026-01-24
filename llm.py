import subprocess


MODEL = "llama3.1:8b"  # change if needed


def ask_llm(prompt: str) -> str:
    try:
        process = subprocess.run(
            ["ollama", "run", MODEL],
            input=prompt,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="ignore"
        )

        if process.returncode != 0:
            return "LLM Error: Failed to generate response."

        output = process.stdout.strip()
        if not output:
            return "LLM Error: Empty response."

        return output

    except Exception as e:
        return f"LLM Exception: {str(e)}"