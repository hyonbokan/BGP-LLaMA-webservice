from app.utils.code_extract import extract_code_from_reply


def test_extracts_python_block():
    reply = "Here you go:\n```python\nprint('hi')\n```\nDone."
    assert extract_code_from_reply(reply) == "print('hi')\n"


def test_returns_first_block_only():
    reply = "```python\na = 1\n```\ntext\n```python\nb = 2\n```"
    assert extract_code_from_reply(reply) == "a = 1\n"


def test_returns_none_without_block():
    assert extract_code_from_reply("no code here") is None


def test_ignores_non_python_fence():
    assert extract_code_from_reply("```js\nvar x = 1;\n```") is None
