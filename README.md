# node-router

Teltonika RUT-360 Data to Server MQTT → renewvan-bus router remap. Bridges
the router's own connectivity feed (RutOS *Data to Server*, server type MQTT)
onto the shared `renewvan/router/<id>/*` schema — no new sensing, just a
payload remap, same shape as `node-battery` but for one broker instead of
two. Per `hub/.scratch/node-router/map.md`.

## One persistent MQTT connection

The hub bus carries both directions on a single connection:

- **Subscribe** `renewvan/router/<id>/raw` (QoS 1) — the topic the RUT's
  Data to Server collection publishes one JSON document to every 60 s
  (`{input:{…}}` keyed by input name).
- **Publish** (retained, JSON-encoded scalars) `renewvan/router/<id>/<property>`
  per the [router schema](https://renewvan.dev/schema/router.schema.json),
  plus node liveness on `renewvan/router/health` (`online`/`offline` via MQTT
  LWT) — deliberately 3 segments, not 4, so it can't be mistaken for a
  `router` entity keyed by a fake `health` id.

## Mapping

| Data to Server key | → property | |
|---|---|---|
| `gsm.rsrp` | `signal_rsrp_dbm` | direct copy |
| `gsm.rsrq` | `signal_rsrq_db` | direct copy |
| `gsm.sinr` | `signal_sinr_db` | direct copy |
| `gsm.rssi` | `signal_rssi_dbm` | direct copy |
| `gsm.operator` | `operator` | direct copy (numeric PLMN, e.g. `26203`) |
| `gsm.conntype` | `network_type` | normalized: `LTE`/`4G` → `lte`, `5G` forms → `nr`, anything else → `unknown` |
| `uptime.uptime` | `uptime_s` | direct copy (seconds) |
| `mobile_usage.tx` | `data_used_month_tx_b` | direct copy (bytes, month window) |
| `mobile_usage.rx` | `data_used_month_rx_b` | direct copy (bytes, month window) |

A source key that is missing or wrongly typed omits its property — never a
fake zero or a coerced string. All other vendor keys (`imei`, `temp`, …)
never reach the bus. The mapping is a pure function
(`node_router/mapping.py`, no network/MQTT client) — this is what
`tests/test_mapping.py` exercises against the live-captured payload
(`tests/fixtures/raw-capture.json`), no broker or router required.

## Configuration

Environment variables (matches `hub`'s `docker-compose.yml` `node-router:`
service block):

| Variable | Default | Notes |
|---|---|---|
| `MQTT_HOST` | `mosquitto` | Renewvan bus broker |
| `MQTT_PORT` | `1883` | |
| `MQTT_USERNAME` | _(none)_ | |
| `MQTT_PASSWORD` | _(none)_ | |
| `ROUTER_ID` | `main` | `renewvan/router/<id>/…` segment; one router per hub |

## Running

```bash
pip install -r requirements.txt
MQTT_HOST=<pi> python -m node_router.main
```

## Testing

```bash
pip install -r requirements.txt -r requirements-test.txt
pytest tests/ -v
```

## Releasing

Tagging a GitHub release builds and publishes
`ghcr.io/<owner>/node-router:<tag>`, which `hub`'s deployment compose
file pins by tag (never builds from source — see
`hub/docs/adr/0001-compose-services-via-pinned-images-not-git-submodules.md`).
