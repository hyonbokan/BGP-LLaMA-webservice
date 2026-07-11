from app.llm.schemas import AnalysisType, BgpIntent, BgpScript, TimeWindow


def test_asn_stripped_and_validated():
    assert BgpIntent(target_asn="AS3356").target_asn == "3356"
    assert BgpIntent(target_asn="as65000").target_asn == "65000"
    assert BgpIntent(target_asn="not-an-asn").target_asn is None
    assert BgpIntent(target_asn=None).target_asn is None


def test_prefixes_filtered_and_deduped():
    i = BgpIntent(prefixes=["192.0.2.0/24", "garbage", "192.0.2.0/24", "2001:db8::/32"])
    assert i.prefixes == ["192.0.2.0/24", "2001:db8::/32"]


def test_time_window_parsed_and_repaired():
    tw = TimeWindow(from_time="2020-01-01", until_time="nonsense")
    assert tw.from_time == "2020-01-01 00:00:00"
    assert tw.until_time is None


def test_unknown_analysis_type_falls_back_to_default():
    assert BgpIntent(analysis_type="wat").analysis_type is AnalysisType.default
    assert BgpIntent().analysis_type is AnalysisType.default


def test_collectors_cleaned_and_deduped():
    i = BgpIntent(collectors=[" rrc00 ", "", "rrc00", "route-views2"])
    assert i.collectors == ["rrc00", "route-views2"]


def test_bgpscript_optional_script():
    s = BgpScript(analysis_type="knowledge", explanation="hi")
    assert s.script is None
    assert s.explanation == "hi"
