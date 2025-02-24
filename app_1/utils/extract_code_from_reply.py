import re

def extract_code_from_reply(assistant_reply_content):
    code_pattern = r"```python\s*\n(.*?)```"
    match = re.search(code_pattern, assistant_reply_content, re.DOTALL)
    if match:
        code = match.group(1)
        return code
    else:
        return None