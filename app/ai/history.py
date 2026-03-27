from collections import deque

_cache: dict[str, deque] = {}
MAX_HISTORY = 5


def get_history(sender_id: str) -> list[dict]:
    """Trả về list các turn gần nhất: [{"role": "user"|"assistant", "text": "..."}]"""
    return list(_cache.get(sender_id, []))


def add_turn(sender_id: str, user_text: str, bot_text: str) -> None:
    if sender_id not in _cache:
        _cache[sender_id] = deque(maxlen=MAX_HISTORY)
    _cache[sender_id].append({"role": "user", "text": user_text})
    _cache[sender_id].append({"role": "assistant", "text": bot_text})


def format_history(history: list[dict]) -> str:
    if not history:
        return ""
    lines = []
    for turn in history:
        prefix = "Khách" if turn["role"] == "user" else "Bot"
        lines.append(f"[{prefix}]: {turn['text']}")
    return "\n".join(lines)
