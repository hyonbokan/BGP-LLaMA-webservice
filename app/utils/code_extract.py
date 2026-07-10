import re

_CODE_PATTERN = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)


def extract_code_from_reply(reply: str):
    """Return the first ```python fenced block in an assistant reply, or None."""
    match = _CODE_PATTERN.search(reply)
    return match.group(1) if match else None
