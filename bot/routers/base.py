from aiogram import Router
from aiogram.enums.chat_type import ChatType

from ..filters import connect_chat_type_filter


class BaseRouter(Router):
    chat_types: ChatType | list[str] | str | None = None

    def __init__(self) -> None:
        """
        Base router class.
        Provides a structured setup for filters, middlewares, handlers, and schedulers,
        with optional overrides for specific setup methods in subclasses.
        """
        super().__init__(name=__name__)
        self._setup()

    def _setup(self):
        """
        Main setup method.
        Calls individual setup methods for routers, filters, middlewares, handlers, and schedulers.
        Subclasses can override individual methods if needed.
        """
        self._include_routers()
        self._setup_filters()
        self.setup_middlewares()
        self.setup_handlers()
        self.setup_scheduler()

    def _include_routers(self):
        """
        Default implementation for including child routers.
        Can be overridden in subclasses if custom logic is needed.
        """
        pass

    def _setup_filters(self):
        """
        Default implementation for setting up custom filters.
        Can be overridden in subclasses if custom filters are required.
        """
        if self.chat_types:
            chat_types = self.chat_types if isinstance(self.chat_types, list) else [self.chat_types]
            connect_chat_type_filter(
                list(self.observers.values()),
                *chat_types
            )

    def setup_middlewares(self):
        """
        Default implementation for configuring middlewares.
        Can be overridden in subclasses to add middlewares.
        """
        pass

    def setup_handlers(self):
        """
        Default implementation for configuring handlers.
        Can be overridden in subclasses to define specific handlers.
        """
        pass

    def setup_scheduler(self):
        """
        Default implementation for setting up a task scheduler.
        Can be overridden in subclasses to configure periodic tasks.
        """
        pass
