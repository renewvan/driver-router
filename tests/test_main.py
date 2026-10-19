import json

import node_router.main as main_module
from node_router.config import AppConfig, MqttConfig


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


def run_node(monkeypatch, node_version: str | None) -> dict:
    StubPublisher.instances.clear()
    if node_version is None:
        monkeypatch.delenv("NODE_VERSION", raising=False)
    else:
        monkeypatch.setenv("NODE_VERSION", node_version)
    monkeypatch.setattr(main_module, "Publisher", StubPublisher)
    monkeypatch.setattr(main_module, "read_host_serial", lambda: None)
    config = AppConfig(mqtt=MqttConfig("localhost", 1883, None, None), router_id="main")
    monkeypatch.setattr(main_module, "load_config", lambda: config)
    main_module.run()
    return json.loads(StubPublisher.instances[0].info)


def test_run_stamps_node_version_env_into_published_info(monkeypatch) -> None:
    info = run_node(monkeypatch, "v9.9.9")
    assert info["version"] == "v9.9.9"
    assert info["node"] == "router"


def test_run_reports_dev_when_node_version_is_unset(monkeypatch) -> None:
    assert run_node(monkeypatch, None)["version"] == "dev"
