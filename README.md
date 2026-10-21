# driver-router

Teltonika RUT-360 Data to Server MQTT → renewvan-bus router remap. Bridges
the router's own connectivity feed (RutOS *Data to Server*, server type MQTT)
onto the shared `renewvan/router/<id>/*` schema — no new sensing, just a
payload remap, same shape as `driver-battery` but for one broker instead of
two. Per `hub/.scratch/node-router/map.md`.

## One persistent MQTT connection

The hub bus carries both directions on a single connection:

- **Subscribe** `renewvan/router/<id>/raw` (QoS 1) — the topic the RUT's
  Data to Server collection publishes one JSON document to every 60 s
  (`{input:{…}}` keyed by input name).
- **Publish** (retained, JSON-encoded scalars) `renewvan/router/<id>/<property>`
  per the [router schema](https://renewvan.dev/schema/router.schema.json),
  plus device liveness on `renewvan/router/health` (`online`/`offline` via MQTT
  LWT) — deliberately 3 segments, not 4, so it can't be mistaken for a
  `router` entity keyed by a fake `health` id.
- **Device info:** `renewvan/router/info` — one retained JSON message
  describing this Device (see [Device info](#device-info)). Published on **every
  connect, immediately before `online`**, so a consumer that sees `online`
  always finds info already retained. It is **never cleared**: it stays
  retained when the Device goes offline or its last will fires, which is what
  lets a consumer show "offline, last seen vX". `renewvan/router/health` is
  unchanged: a bare `online`/`offline`.

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
(`driver_router/mapping.py`, no network/MQTT client) — this is what
`tests/test_mapping.py` exercises against the live-captured payload
(`tests/fixtures/raw-capture.json`), no broker or router required.

## Configuration

Environment variables (matches `hub`'s `docker-compose.yml` `driver-router:`
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
MQTT_HOST=<pi> python -m driver_router.main
```

## Testing

```bash
pip install -r requirements.txt -r requirements-test.txt
pytest tests/ -v
```

## Releasing

Tagging a GitHub release builds and publishes
`ghcr.io/<owner>/driver-router:<tag>`, which `hub`'s deployment compose
file pins by tag (never builds from source — see
`hub/docs/adr/0001-compose-services-via-pinned-images-not-git-submodules.md`).

The release workflow passes the tag as the `DEVICE_VERSION` build argument, which
the Dockerfile promotes to an environment variable the Device reads (see
[Device info](#device-info)). Nothing else carries a version.

## Device info

The Device describes itself to the dashboard with a manifest plus two runtime
values. Contract: `hub`'s `schema/device-info.schema.json` (decision record:
`hub/docs/adr/0011-node-manifest-and-retained-info-topic.md`).

**`manifest.json`** (repo root) is the single source of the static fields:
`device` (`router`, the topic key), `product`, `source`, `publishes`, and
optional `manufacturer` / `homepage`. `version` and `board_serial` are
**forbidden** in it. The image build copies it beside the module
(`driver_router/manifest.json`); the Device reads that copy first and falls back
to the repo-root file for a checkout run.

**`version`** comes from the git release tag and nowhere else. The release
workflow passes it as the `DEVICE_VERSION` build argument, which becomes an
environment variable the Device reads. When `DEVICE_VERSION` is unset or empty (a
checkout run, a local `docker build`) the Device reports the literal **`dev`**.
There is no `version` file or `__version__`, and the `pyproject.toml` version
is a fixed placeholder nothing reads.

**`board_serial`** is the `Serial` line of the host's `/proc/cpuinfo`, read once
at start. A default container can read it, so no compose or Dockerfile mount
change is needed. It is **omitted** (never faked, never `unknown`) when the
file is unreadable, the line is missing or empty, or the value is all zeros.

`driver_router/device_info.py` is a small helper deliberately **copied** into each
Python device repo rather than shared as a package, so each Device releases
independently.

**CI gate:** `.github/workflows/manifest.yml` validates `manifest.json`
against `device-manifest.schema.json`, fetched from `hub` at a **pinned commit**
(`HUB_REF`) with `ajv-cli`, and fails if a manifest containing `version` is
accepted. Bump `HUB_REF` deliberately to adopt a newer contract. To check
locally:

```bash
npx --yes ajv-cli@5 validate -s path/to/hub/schema/device-manifest.schema.json -d manifest.json
```
