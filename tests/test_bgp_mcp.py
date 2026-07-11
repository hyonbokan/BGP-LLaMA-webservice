from bgp_mcp.records import collect_records, element_to_record


class _Elem:
    """A duck-typed stand-in for a pybgpstream BGPElem (no native library needed)."""

    def __init__(self, time, type_, peer_asn, fields):
        self.time = time
        self.type = type_
        self.peer_asn = peer_asn
        self.fields = fields


def test_announcement_record_has_origin_and_path():
    elem = _Elem(
        1_700_000_000,
        "A",
        3333,
        {"prefix": "8.8.8.0/24", "as-path": "3356 15169", "communities": [], "med": None},
    )
    record = element_to_record(elem)
    assert record["type"] == "A"
    assert record["prefix"] == "8.8.8.0/24"
    assert record["as_path"] == ["3356", "15169"]
    assert record["origin"] == "15169"
    assert record["peer_asn"] == "3333"


def test_withdrawal_record_has_no_origin_or_path():
    elem = _Elem(1_700_000_050, "W", 3333, {"prefix": "8.8.8.0/24"})
    record = element_to_record(elem)
    assert record["type"] == "W"
    assert record["as_path"] == []
    assert record["origin"] is None


def test_communities_are_json_safe_strings():
    elem = _Elem(1, "A", 1, {"prefix": "1.1.1.0/24", "as-path": "13335", "communities": [("3356", "100")]})
    record = element_to_record(elem)
    assert all(isinstance(c, str) for c in record["communities"])


def test_collect_records_truncates_at_max():
    elems = [_Elem(i, "A", 1, {"prefix": "1.1.1.0/24", "as-path": "13335"}) for i in range(10)]
    records, truncated = collect_records(elems, max_records=3)
    assert len(records) == 3
    assert truncated is True


def test_collect_records_under_cap_is_not_truncated():
    elems = [_Elem(i, "A", 1, {"prefix": "1.1.1.0/24", "as-path": "13335"}) for i in range(2)]
    records, truncated = collect_records(elems, max_records=5)
    assert len(records) == 2
    assert truncated is False
