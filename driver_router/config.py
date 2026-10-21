"""Config sourced from environment variables — matches `hub`'s
`docker-compose.yml` `driver-router:` service block, the contract between this
repo and the deployment manifest. One MQTT connection: the hub bus carries
both the RUT's raw feed (subscribe) and the normalized publishes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MqttConfig:
    host: str
    port: int
    username: str | None
    password: str | None


@dataclass(frozen=True)
class AppConfig:
    mqtt: MqttConfig
    router_id: str


def load_config() -> AppConfig:
    return AppConfig(
        mqtt=MqttConfig(
            host=os.environ.get("MQTT_HOST", "mosquitto"),
            port=int(os.environ.get("MQTT_PORT", "1883")),
            username=os.environ.get("MQTT_USERNAME") or None,
            password=os.environ.get("MQTT_PASSWORD") or None,
        ),
        router_id=os.environ.get("ROUTER_ID", "main"),
    )
