#!/usr/bin/env python3
"""node-router entrypoint."""

from __future__ import annotations

import argparse
import logging
import os

from node_router.config import load_config
from node_router.node_info import build_info, read_host_serial
from node_router.publisher import Publisher
from node_router.subscriber import Subscriber


def run() -> None:
    config = load_config()
    # Version is stamped by the release build (NODE_VERSION); unset reports "dev".
    # Host serial is read once, here, at process start.
    info = build_info(os.environ.get("NODE_VERSION"), read_host_serial())
    publisher = Publisher(config.mqtt, info)
    Subscriber(config, publisher)
    publisher.connect()
    try:
        publisher.run_forever()
    finally:
        publisher.disconnect()


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

    run()


if __name__ == "__main__":
    main()
