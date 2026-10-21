"""Pure mapping: Teltonika RUT-360 Data to Server JSON -> `renewvan/router/<id>/*`
publishes. No network, no MQTT client — this is the seam the tests exercise
against the live-captured payload (`tests/fixtures/raw-capture.json`).

Source payload is one RutOS "Data to Server" MQTT message, Send-as-object
form `{input:{…}}` keyed by input name (`gsm`, `mobile_usage`, `uptime`).
Field list per the settled Router contract
(`hub/.scratch/node-router/issues/02-settle-router-fields.md`): a source key
that is missing or wrongly typed omits its property — never a fake zero or a
coerced string.
"""

from __future__ import annotations

# gsm member -> router property. Direct copies: the modem reports bare
# integers in dBm/dB already matching the schema's sign convention.
_GSM_NUMBERS: dict[str, str] = {
    "rsrp": "signal_rsrp_dbm",
    "rsrq": "signal_rsrq_db",
    "sinr": "signal_sinr_db",
    "rssi": "signal_rssi_dbm",
}

# mobile_usage member (bytes, calendar-month window) -> router property.
_MONTH_NUMBERS: dict[str, str] = {
    "tx": "data_used_month_tx_b",
    "rx": "data_used_month_rx_b",
}

# Modem conntype (lowercased) -> network_type enum. 4G is the LTE family and
# RutOS emits it for either string; 5G forms are NR. Anything else —
# "no service", unparseable — falls back to `unknown` (battery's
# forward-compat pattern).
_NETWORK_TYPES: dict[str, str] = {
    "2g": "2g",
    "3g": "3g",
    "lte": "lte",
    "4g": "lte",
    "5g": "nr",
    "5g sa": "nr",
    "nr": "nr",
}


def router_topic(router_id: str, prop: str) -> str:
    return f"renewvan/router/{router_id}/{prop}"


def network_type(conntype: object) -> str:
    """Normalize the modem's conntype value to the `network_type` enum."""
    if not isinstance(conntype, str):
        return "unknown"
    return _NETWORK_TYPES.get(conntype.strip().lower(), "unknown")


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _section(payload: dict, name: str) -> dict | None:
    """One Data to Server input section. Object form is the norm; an array
    batches multiple periods (segment count > 1) — only the newest (last)
    segment is mapped. Anything else is absent.
    """
    value = payload.get(name)
    if isinstance(value, list):
        value = value[-1] if value else None
    return value if isinstance(value, dict) else None


def map_raw(payload: dict, router_id: str) -> list[tuple[str, object]]:
    """Map a decoded Data to Server payload to `(topic, value)` pairs for the
    settled Router properties."""
    if not isinstance(payload, dict):
        return []

    results: list[tuple[str, object]] = []

    gsm = _section(payload, "gsm")
    if gsm is not None:
        for member, prop in _GSM_NUMBERS.items():
            if _is_number(gsm.get(member)):
                results.append((router_topic(router_id, prop), gsm[member]))
        if isinstance(gsm.get("operator"), str):
            results.append((router_topic(router_id, "operator"), gsm["operator"]))
        if "conntype" in gsm:
            results.append((router_topic(router_id, "network_type"), network_type(gsm["conntype"])))

    usage = _section(payload, "mobile_usage")
    if usage is not None:
        for member, prop in _MONTH_NUMBERS.items():
            if _is_number(usage.get(member)):
                results.append((router_topic(router_id, prop), usage[member]))

    uptime = _section(payload, "uptime")
    if uptime is not None and _is_number(uptime.get("uptime")):
        results.append((router_topic(router_id, "uptime_s"), uptime["uptime"]))

    return results
