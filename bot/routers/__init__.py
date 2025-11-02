from __future__ import annotations

from aiogram import Dispatcher

from .admin_router import AdminRouter


def setup_routers(dispatcher: Dispatcher) -> None:
    """Attach all application routers to the given dispatcher."""
    routers = [
        AdminRouter(),
    ]

    for router in routers:
        dispatcher.include_router(router)


__all__ = ["setup_routers"]
