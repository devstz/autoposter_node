from __future__ import annotations

import asyncio
import logging

from bootstrap import init_app

logger = logging.getLogger(__name__)


def main() -> None:
    try:
        asyncio.run(init_app())
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")


if __name__ == "__main__":
    main()
