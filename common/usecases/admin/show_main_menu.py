from __future__ import annotations

from typing import Dict

from common.dto import MenuItemDTO, MenuViewDTO
from common.enums import AdminMenuAction


class ShowMainMenuUseCase:
    def __init__(
        self,
        *,
        prompt_text: str,
        buttons: Dict[AdminMenuAction, str],
    ) -> None:
        self._prompt_text = prompt_text
        self._buttons = buttons

    async def __call__(self) -> MenuViewDTO:
        def btn(action: AdminMenuAction) -> MenuItemDTO:
            label = self._buttons.get(action, action.value.title())
            return MenuItemDTO(label=label, action=action)

        rows = [
            [btn(AdminMenuAction.DISTRIBUTIONS)],
            [btn(AdminMenuAction.BOTS), btn(AdminMenuAction.GROUPS)],
            [btn(AdminMenuAction.STATS)],
            [btn(AdminMenuAction.SETTINGS)],
        ]
        return MenuViewDTO(text=self._prompt_text, rows=rows)
