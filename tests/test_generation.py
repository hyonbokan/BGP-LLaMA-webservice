from app.llm.generation import sanitize_script, script_syntax_error


def test_rewrites_leaked_personal_path():
    script = 'directory = "/home/hb/ris_bgp_updates/2024/01/rrc00"\n'
    assert sanitize_script(script) == 'directory = "/data/bgp/2024/01/rrc00"\n'


def test_rewrites_leak_for_any_username():
    script = 'p = "/home/someone.else/ris_bgp_updates/2024/01/rrc00"'
    out = sanitize_script(script)
    assert "/home/" not in out
    assert "/data/bgp/2024/01/rrc00" in out


def test_leaves_unrelated_paths_and_none_alone():
    assert sanitize_script("path = '/tmp/output.json'") == "path = '/tmp/output.json'"
    assert sanitize_script(None) is None
    assert sanitize_script("") == ""


def test_syntax_error_detects_broken_script():
    assert script_syntax_error("def broken(") is not None
    assert script_syntax_error("x = 1\n") is None
    assert script_syntax_error(None) is None
