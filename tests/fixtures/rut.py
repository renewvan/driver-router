"""Fixture Teltonika RUT-360 Data to Server payloads (one JSON document per
60 s period, Send-as-object form `{input:{…}}`).

`RAW_CAPTURE` is the byte-identical live capture from the router
(`hub/.scratch/node-router/research/raw-capture.json`, 2026-10-02) — the
all-members gsm sender form. `RAW_CAPTURE_RESTRICTED` is the steady-state
production form after the sender was restricted to the settled members.
"""

import json
from pathlib import Path

_FIXTURES = Path(__file__).parent

RAW_CAPTURE = json.loads((_FIXTURES / "raw-capture.json").read_text(encoding="utf-8"))

RAW_CAPTURE_RESTRICTED = {
    "gsm": {
        "rssi": -54,
        "rsrp": -85,
        "sinr": 6,
        "rsrq": -10,
        "operator": "26203",
        "conntype": "LTE",
    },
    "mobile_usage": {"tx": 140194858, "rx": 385092522},
    "uptime": {"uptime": 826671},
}

# Array-of-segments form: RutOS batches periods into an array when a sender's
# segment count is >1 — only the newest (last) segment may be mapped.
SEGMENTED_CAPTURE = {
    "gsm": [
        {"rsrp": -111, "rsrq": -16, "sinr": -3, "rssi": -89, "operator": "26201", "conntype": "3G"},
        {"rsrp": -85, "rsrq": -10, "sinr": 6, "rssi": -54, "operator": "26203", "conntype": "LTE"},
    ],
    "mobile_usage": [
        {"tx": 1, "rx": 2},
        {"tx": 140194858, "rx": 385092522},
    ],
    "uptime": [{"uptime": 100}, {"uptime": 826671}],
}

# The string-with-unit form RutOS does NOT emit today (values are bare
# integers) but could under firmware drift — dropped, never coerced.
STRING_SIGNAL_CAPTURE = {
    "gsm": {"rsrp": "-85 dBm", "rssi": -54, "operator": "26203", "conntype": "LTE"},
    "mobile_usage": {"tx": 1, "rx": 2},
    "uptime": {"uptime": 5},
}

UPTIME_ONLY_CAPTURE = {"uptime": {"uptime": 42}}
