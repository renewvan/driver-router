import json

import driver_router.main as main_module
from driver_router.config import AppConfig, MqttConfig


class StubPublisher:
    """Stands in for the MQTT connection; captures the info it was constructed with."""

    instances: list["StubPublisher"] = []

    def __init__(self, mqtt_config, info: str) -> None:
        self.info = info
        StubPublisher.instances.append(self)

    def connect(self) -> None: ...
    def run_forever(self) -> None: ...
    def disconnect(self) -> None: ...
    def subscribe(self, topic, callback) -> None: ...


def run_device(monkeypatch, device_version: str | None, board_serial: str | None = None) -> dict:
    StubPublisher.instances.clear()
    if device_version is None:
        monkeypatch.delenv("DEVICE_VERSION", raising=False)
    else:
        monkeypatch.setenv("DEVICE_VERSION", device_version)
    monkeypatch.setattr(main_module, "Publisher", StubPublisher)
    monkeypatch.setattr(main_module, "read_board_serial", lambda: board_serial)
    config = AppConfig(mqtt=MqttConfig("localhost", 1883, None, None), router_id="main")
    monkeypatch.setattr(main_module, "load_config", lambda: config)
    main_module.run()
    return json.loads(StubPublisher.instances[0].info)


def test_run_stamps_device_version_env_into_published_info(monkeypatch) -> None:
    info = run_device(monkeypatch, "v9.9.9")
    assert info["version"] == "v9.9.9"
    assert info["device"] == "router"


def test_run_reports_dev_when_device_version_is_unset(monkeypatch) -> None:
    assert run_device(monkeypatch, None)["version"] == "dev"


def test_run_publishes_the_board_serial_when_known(monkeypatch) -> None:
    assert run_device(monkeypatch, "v1", "00000000a1b2c3d4")["board_serial"] == "00000000a1b2c3d4"


def test_run_omits_board_serial_when_unknown(monkeypatch) -> None:
    assert "board_serial" not in run_device(monkeypatch, "v1", None)
