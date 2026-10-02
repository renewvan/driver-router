#!/usr/bin/env python3
"""node-router entrypoint."""

from __future__ import annotations

import argparse
import logging

from node_router.config import load_config
from node_router.publisher import Publisher
from node_router.subscriber import Subscriber


def main() -> None:
    parser = argparse.ArgumentParser(
        description="node-router: RUT-360 Data to Server MQTT -> renewvan-bus router remap"
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
    )

    config = load_config()
    publisher = Publisher(config.mqtt)
    Subscriber(config, publisher)
    publisher.connect()
    try:
        publisher.run_forever()
    finally:
        publisher.disconnect()


if __name__ == "__main__":
    main()
