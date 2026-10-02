"""Fixture-payload tests for the RUT-360 Data to Server →
`renewvan/router/<id>/*` mapping — no live broker or router required.

Expected values come from the settled field list
(`hub/.scratch/node-router/issues/02-settle-router-fields.md`) applied to the
real captured payload, not from re-reading the mapping code.
"""

from node_router.mapping import map_raw
from tests.fixtures import rut as fx

ROUTER_ID = "main"


def pairs(payload):
    return dict(map_raw(payload, ROUTER_ID))


def prop(name):
    return f"renewvan/router/{ROUTER_ID}/{name}"


def test_live_capture_maps_all_nine_properties():
    p = pairs(fx.RAW_CAPTURE)
    assert p[prop("signal_rsrp_dbm")] == -85
    assert p[prop("signal_rsrq_db")] == -10
    assert p[prop("signal_sinr_db")] == 6
    assert p[prop("signal_rssi_dbm")] == -54
    assert p[prop("operator")] == "26203"
    assert p[prop("network_type")] == "lte"
    assert p[prop("uptime_s")] == 826671
    assert p[prop("data_used_month_tx_b")] == 140194858
    assert p[prop("data_used_month_rx_b")] == 385092522
    assert len(p) == 9


def test_restricted_sender_payload_maps_the_same_nine():
    # Steady-state device form after the gsm sender was restricted to the
    # settled members — identical output to the all-members capture.
    assert pairs(fx.RAW_CAPTURE_RESTRICTED) == pairs(fx.RAW_CAPTURE)


def test_unmapped_vendor_keys_never_reach_the_bus():
    p = pairs(fx.RAW_CAPTURE)
    assert not any(topic.endswith(("rscp", "ecio", "imei", "conntype")) for topic in p)


def test_array_segments_map_only_the_newest():
    p = pairs(fx.SEGMENTED_CAPTURE)
    assert p[prop("signal_rsrp_dbm")] == -85
    assert p[prop("data_used_month_tx_b")] == 140194858
    assert p[prop("uptime_s")] == 826671
    assert p[prop("network_type")] == "lte"


def test_conntype_normalization():
    assert pairs({"gsm": {"conntype": "LTE"}})[prop("network_type")] == "lte"
    assert pairs({"gsm": {"conntype": "4G"}})[prop("network_type")] == "lte"
    assert pairs({"gsm": {"conntype": "5G"}})[prop("network_type")] == "nr"
    assert pairs({"gsm": {"conntype": "5G SA"}})[prop("network_type")] == "nr"
    assert pairs({"gsm": {"conntype": "3G"}})[prop("network_type")] == "3g"
    assert pairs({"gsm": {"conntype": "No service"}})[prop("network_type")] == "unknown"
    assert pairs({"gsm": {"conntype": None}})[prop("network_type")] == "unknown"


def test_missing_conntype_omits_network_type():
    assert prop("network_type") not in pairs({"gsm": {"rsrp": -85}})


def test_string_valued_signal_is_dropped_not_coerced():
    p = pairs(fx.STRING_SIGNAL_CAPTURE)
    assert prop("signal_rsrp_dbm") not in p
    assert p[prop("signal_rssi_dbm")] == -54


def test_missing_sections_omit_their_properties():
    assert pairs(fx.UPTIME_ONLY_CAPTURE) == {prop("uptime_s"): 42}


def test_non_object_payload_maps_to_nothing():
    assert map_raw([], ROUTER_ID) == []
    assert map_raw("junk", ROUTER_ID) == []
