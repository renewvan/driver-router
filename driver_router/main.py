#!/usr/bin/env python3
"""driver-router entrypoint."""

from __future__ import annotations

import argparse
import logging
import os

from driver_router.config import load_config
from driver_router.driver_info import build_info, read_board_serial
from driver_router.publisher import Publisher
from driver_router.subscriber import Subscriber


def run() -> None:
    config = load_config()
    # Version is stamped by the release build (DRIVER_VERSION); unset reports "dev".
    # Board serial is read once, here, at process start.
    info = build_info(os.environ.get("DRIVER_VERSION"), read_board_serial())
    publisher = Publisher(config.mqtt, info, config.router_id)
    Subscriber(config, publisher)
    publisher.connect()
    try:
        publisher.run_forever()
    finally:
        publisher.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="driver-router: RUT-360 Data to Server MQTT -> renewvan-bus router remap"
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
