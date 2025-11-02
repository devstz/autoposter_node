from __future__ import annotations

from typing import Dict

from common.enums import AdminMenuAction


class ShowPlaceholderUseCase:
    def __init__(self, *, texts: Dict[AdminMenuAction | str, str]) -> None:
        self._texts = texts

    async def __call__(self, action: AdminMenuAction) -> str:
        return self._texts.get(action) or self._texts.get("placeholder") or "Раздел в разработке"
