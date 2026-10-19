"""Persistent MQTT connection to the renewvan bus — the single connection
this node uses (raw subscribe in, normalized publishes out). LWT on the
router health topic, retained publishes, and callback subscriptions that
survive reconnects. Same shape as node-tank's publisher.py.
"""

from __future__ import annotations

import json
import logging
from typing import Callable

import paho.mqtt.client as mqtt

from node_router.config import MqttConfig

logger = logging.getLogger(__name__)

HEALTH_TOPIC = "renewvan/router/health"
INFO_TOPIC = "renewvan/router/info"


class Publisher:
    def __init__(self, config: MqttConfig, info: str) -> None:
        self._config = config
        self._info = info
        self._client = mqtt.Client(client_id="node-router", clean_session=False)
        if config.username:
            self._client.username_pw_set(config.username, config.password)
        self._client.will_set(HEALTH_TOPIC, payload="offline", qos=1, retain=True)
        self._client.reconnect_delay_set(min_delay=1, max_delay=30)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._subscriptions: dict[str, Callable[[str], None]] = {}

    def _on_connect(self, client, userdata, flags, rc):  # noqa: ANN001
        if rc == 0:
            logger.info(
                "Connected to renewvan-bus MQTT broker %s:%s", self._config.host, self._config.port
            )
            # Info first, then online: a consumer that sees online always finds info
            # retained. Never cleared on offline or by the will ("last seen vX").
            client.publish(INFO_TOPIC, payload=self._info, qos=1, retain=True)
            client.publish(HEALTH_TOPIC, payload="online", qos=1, retain=True)
            for topic in self._subscriptions:
                client.subscribe(topic, qos=1)
        else:
            logger.error("Renewvan-bus MQTT connect failed with rc=%s", rc)

    def _on_message(self, client, userdata, msg):  # noqa: ANN001
        callback = self._subscriptions.get(msg.topic)
        if callback is None:
            logger.debug("Ignoring message on unsubscribed topic %s", msg.topic)
            return
        try:
            callback(msg.payload.decode("utf-8", errors="replace"))
        except Exception:
            logger.exception("Error handling message on topic %s", msg.topic)

    def connect(self) -> None:
        self._client.connect(self._config.host, self._config.port)

    def run_forever(self) -> None:
        self._client.loop_forever()

    def publish(self, topic: str, payload: object) -> None:
        self._client.publish(topic, payload=json.dumps(payload), qos=1, retain=True)

    def subscribe(self, topic: str, callback: Callable[[str], None]) -> None:
        """Register a topic callback; subscribed on connect and re-subscribed
        on every reconnect."""
        self._subscriptions[topic] = callback
        self._client.subscribe(topic, qos=1)
        logger.info("Subscribed to %s", topic)

    def disconnect(self) -> None:
        self._client.publish(HEALTH_TOPIC, payload="offline", qos=1, retain=True)
        self._client.disconnect()
