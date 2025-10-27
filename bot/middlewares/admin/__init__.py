from aiogram import Router

from .admin_check_middleware import AdminCheckMiddleware


def connect_admin_middlewares(router: Router):
    admin_check_middleware = AdminCheckMiddleware()
    for observer in router.observers.keys():
        router.observers[observer].middleware.register(admin_check_middleware)