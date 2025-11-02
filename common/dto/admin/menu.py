from __future__ import annotations

from dataclasses import dataclass
from typing import List

from common.enums import AdminMenuAction

@dataclass(slots=True)
class MenuItemDTO:
    label: str
    action: AdminMenuAction


@dataclass(slots=True)
class MenuViewDTO:
    text: str
    rows: List[List[MenuItemDTO]]
