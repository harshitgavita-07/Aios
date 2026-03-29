import json

def run_think(payload: str) -> str:
    """Validate a simple think payload and return a status.

    Expected payload format (JSON string):
    {"thought": "..."}
    """
    try:
        data = json.loads(payload)
        thought = data.get("thought")
        if not thought:
            raise ValueError("'thought' field missing or empty")
        return json.dumps({"status": "ok", "thought": thought})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})
