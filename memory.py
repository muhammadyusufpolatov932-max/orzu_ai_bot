from collections import defaultdict

from config import MAX_HISTORY

_memory = defaultdict(list)


def add_message(user_id: int, role: str, content: str):
    _memory[user_id].append(
        {
            "role": role,
            "content": content,
        }
    )

    if len(_memory[user_id]) > MAX_HISTORY:
        _memory[user_id] = _memory[user_id][-MAX_HISTORY:]


def get_history(user_id: int):
    return list(_memory[user_id])


def clear_history(user_id: int):
    _memory[user_id] = []
