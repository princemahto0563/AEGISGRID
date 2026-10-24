"""
Unit tests for deterministic cascade analysis.
"""

from analysis import analyze_cascade, load_model, validate_asset_id


def test_validate_asset_id():
    model = load_model()

    # Valid registered assets
    for asset_id in ["S-01", "W-02", "T-04", "H-01", "G-01"]:
        is_valid, err = validate_asset_id(asset_id, model)
        assert is_valid is True
        assert err is None

    # Invalid assets
    for bad_id in ["UNKNOWN-999", "X-99", "INVALID", "", "123"]:
        is_valid, err = validate_asset_id(bad_id, model)
        assert is_valid is False
        assert "not registered" in err.lower()


def test_s01_failure_and_downstream_impact():
    model = load_model()
    result = analyze_cascade("S-01", model)

    assert result["is_valid"] is True
    assert result["quarantined"] is False
    assert result["root_asset"] == "S-01"
    assert result["status"] == "ANALYZED"

    # S-01 feeds W-02, T-04, and H-01
    affected_ids = {a["asset_id"] for a in result["affected_assets"]}
    assert "W-02" in affected_ids
    assert "T-04" in affected_ids
    assert "H-01" in affected_ids

    # G-01 is a backup source, not downstream of S-01 in outage cascade
    assert "G-01" not in affected_ids

    # Check impact reasons
    for aff in result["affected_assets"]:
        if aff["asset_id"] == "W-02":
            assert "water pump" in aff["impact_reason"].lower()
        elif aff["asset_id"] == "T-04":
            assert "signal" in aff["impact_reason"].lower()
        elif aff["asset_id"] == "H-01":
            assert "hospital" in aff["impact_reason"].lower() or "grid" in aff["impact_reason"].lower()


def test_unknown_asset_rejection():
    model = load_model()
    for bad_asset in ["UNKNOWN-999", "X-99", "SYNTHETIC-001"]:
        result = analyze_cascade(bad_asset, model)
        assert result["is_valid"] is False
        assert result["quarantined"] is True
        assert result["status"] == "QUARANTINED"
        assert len(result["affected_assets"]) == 0
        assert "quarantin" in result["summary"].lower()
        assert "unregistered" in result["error"].lower() or "not registered" in result["error"].lower()


def test_g01_unavailable_impact():
    model = load_model()
    # When G-01 is failed/unavailable
    result = analyze_cascade("G-01", model)

    assert result["is_valid"] is True
    affected_ids = {a["asset_id"] for a in result["affected_assets"]}
    # Only H-01 is directly dependent on G-01 for reserve power
    assert "H-01" in affected_ids
    assert "S-01" not in affected_ids
    assert "W-02" not in affected_ids
    assert "T-04" not in affected_ids


def test_double_contingency_s01_and_g01_unavailable():
    model = load_model()
    # Both S-01 is out and G-01 is unavailable
    result = analyze_cascade("S-01", model, unavailable_resources={"G-01"})

    assert result["is_valid"] is True
    # H-01 should now be at Critical severity
    h01_aff = next(a for a in result["affected_assets"] if a["asset_id"] == "H-01")
    assert h01_aff["severity"] == "Critical"
    assert "critical risk" in h01_aff["impact_reason"].lower()
