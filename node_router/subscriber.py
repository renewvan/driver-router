"""Subscription of the RUT's raw Data to Server topic on the hub bus and
republish of the mapped, retained properties over the same node's Publisher.

Thin I/O adapter around paho-mqtt; not unit-tested (see mapping.py for the
tested seam).
"""

from __future__ import annotations

import json
import logging

from node_router.config import AppConfig
from node_router.mapping import map_raw
from node_router.publisher import Publisher

logger = logging.getLogger(__name__)


def raw_topic(router_id: str) -> str:
    return f"renewvan/router/{router_id}/raw"


class Subscriber:
    def __init__(self, config: AppConfig, publisher: Publisher) -> None:
        self._router_id = config.router_id
        self._publisher = publisher
        self._raw_topic = raw_topic(config.router_id)
        publisher.subscribe(self._raw_topic, self._on_raw)

    def _on_raw(self, payload: str) -> None:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            logger.warning("Malformed Data to Server payload on %s", self._raw_topic)
            return

        for topic, value in map_raw(data, self._router_id):
            self._publisher.publish(topic, value)
