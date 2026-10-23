import json

import driver_router.main as main_module
from driver_router.config import AppConfig, MqttConfig


class StubPublisher:
    """Stands in for the MQTT connection; captures the info it was constructed with."""

    instances: list["StubPublisher"] = []

    def __init__(self, mqtt_config, info: str, router_id: str) -> None:
        self.info = info
        self.router_id = router_id
        StubPublisher.instances.append(self)

    def connect(self) -> None: ...
    def run_forever(self) -> None: ...
    def disconnect(self) -> None: ...
    def subscribe(self, topic, callback) -> None: ...


def run_driver(monkeypatch, driver_version: str | None, board_serial: str | None = None) -> dict:
    StubPublisher.instances.clear()
    if driver_version is None:
        monkeypatch.delenv("DRIVER_VERSION", raising=False)
    else:
        monkeypatch.setenv("DRIVER_VERSION", driver_version)
    monkeypatch.setattr(main_module, "Publisher", StubPublisher)
    monkeypatch.setattr(main_module, "read_board_serial", lambda: board_serial)
    config = AppConfig(mqtt=MqttConfig("localhost", 1883, None, None), router_id="main")
    monkeypatch.setattr(main_module, "load_config", lambda: config)
    main_module.run()
    return json.loads(StubPublisher.instances[0].info)


def test_run_stamps_driver_version_env_into_published_info(monkeypatch) -> None:
    info = run_driver(monkeypatch, "v9.9.9")
    assert info["version"] == "v9.9.9"
    assert info["driver"] == "router"


def test_run_reports_dev_when_driver_version_is_unset(monkeypatch) -> None:
    assert run_driver(monkeypatch, None)["version"] == "dev"


def test_run_publishes_the_board_serial_when_known(monkeypatch) -> None:
    assert run_driver(monkeypatch, "v1", "00000000a1b2c3d4")["board_serial"] == "00000000a1b2c3d4"


def test_run_omits_board_serial_when_unknown(monkeypatch) -> None:
    assert "board_serial" not in run_driver(monkeypatch, "v1", None)


def test_run_hands_the_configured_router_id_to_the_publisher(monkeypatch) -> None:
    run_driver(monkeypatch, "v1")
    assert StubPublisher.instances[0].router_id == "main"
