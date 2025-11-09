from __future__ import annotations

from typing import Final


BUTTONS: Final[dict[str, dict[str, str]]] = {
    "menu": {
        "distributions": "📢 Рассылки",
        "bots": "🤖 Боты",
        "groups": "👥 Группы",
        "stats": "📊 Статистика",
        "settings": "⚙️ Настройки",
    },
    "groups": {
        "add_bindings": "➕ Добавить привязки групп",
        "list_bindings": "📋 Список привязок",
        "choose_bot": "Выбрать бота",
        "refresh": "🔄 Обновить",
        "unbind": "🔓 Отвязать",
        "back_to_list": "⬅️ К списку",
    },
    "distributions": {
        "create": "🆕 Создать рассылку",
        "list": "📋 Список рассылок",
        "auto_name": "📝 Автоназвание",
        "mode_create": "🆕 Новые посты",
        "mode_replace": "♻️ Заменить посты",
        "target_groups": "👥 Выбрать группы",
        "target_bots": "🤖 Выбрать ботов",
        "target_all": "🌐 Все группы",
        "back": "⬅️ Назад",
        "cancel": "↩️ Отмена",
        "continue": "✅ Продолжить",
        "refresh": "🔄 Обновить",
        "back_to_list": "⬅️ К списку",
        "back_to_menu": "⬅️ В меню",
        "stop_all": "⏸ Остановить все",
        "start_all": "▶️ Запустить все",
        "enable_notify": "🔔 Включить уведомления",
        "disable_notify": "🔕 Выключить уведомления",
        "groups": "📋 Список групп",
        "delete": "🗑 Удалить",
        "back_to_card": "⬅️ К рассылке",
        "back_to_groups": "⬅️ К группам",
    },
    "common": {
        "back": "⬅️ Назад",
        "cancel": "↩️ Отмена",
    },
    "bots": {
        "list": "📋 Список ботов",
        "add_stub": "➕ Добавить бота (в разработке)",
        "free_posts": "🧹 Освободить от постов",
        "delete": "🗑 Удалить бота",
        "distribution_preview": "🧮 Автораспределение",
    },
    "confirm": {
        "yes": "✅ Да",
        "no": "🚫 НЕТ",
        "mode_instant": "⚡️ Мгновенно",
        "mode_graceful": "🕰 Аккуратно",
        "apply": "✅ Подтвердить",
        "decline": "↩️ Отмена",
    },
    "pagination": {
        "prev": "⬅️",
        "next": "➡️",
        "indicator": "{current}/{total}",
    },
    "distribution": {
        "apply": "✅ Применить распределение",
        "cancel": "↩️ Отменить",
    },
}
