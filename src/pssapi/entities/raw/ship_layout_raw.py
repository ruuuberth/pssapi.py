"""
This file has been generated automatically
"""

from typing import Any as _Any
from typing import Dict as _Dict

from ...types import EntityInfo as _EntityInfo
from ...utils import parse as _parse
from .entity_base_raw import EntityBaseRaw as _EntityBaseRaw


class ShipLayoutRaw(_EntityBaseRaw):
    XML_NODE_NAME: str = "ShipLayout"

    def __init__(self, ship_layout_info: _EntityInfo) -> None:
        self._dict: _Dict[str, _Any] = {}
        self._ship_layout_id: int = _parse.pss_int(ship_layout_info.pop("ShipLayoutId", None))
        self._ship_id: int = _parse.pss_int(ship_layout_info.pop("ShipId", None))
        self._ship_design_id: int = _parse.pss_int(ship_layout_info.pop("ShipDesignId", None))
        self._xml: str = _parse.pss_str(ship_layout_info.pop("Xml", None))
        self._ship_layout_name: str = _parse.pss_str(ship_layout_info.pop("ShipLayoutName", None))
        self._ship_layout_type: str = _parse.pss_str(ship_layout_info.pop("ShipLayoutType", None))
        self._has_lab_room: bool = _parse.pss_bool(ship_layout_info.pop("HasLabRoom", None))
        super().__init__(ship_layout_info)

    @property
    def ship_layout_id(self) -> int:
        return self._ship_layout_id

    @property
    def ship_id(self) -> int:
        return self._ship_id

    @property
    def ship_design_id(self) -> int:
        return self._ship_design_id

    @property
    def xml(self) -> str:
        return self._xml

    @property
    def ship_layout_name(self) -> str:
        return self._ship_layout_name

    @property
    def ship_layout_type(self) -> str:
        return self._ship_layout_type

    @property
    def has_lab_room(self) -> bool:
        return self._has_lab_room

    def _key(self):
        return (self.ship_layout_id,)

    def __dict__(self):
        if not self._dict:
            self._dict = {
                "ShipLayoutId": self.ship_layout_id,
                "ShipId": self.ship_id,
                "ShipDesignId": self.ship_design_id,
                "Xml": self.xml,
                "ShipLayoutName": self.ship_layout_name,
                "ShipLayoutType": self.ship_layout_type,
                "HasLabRoom": self.has_lab_room,
            }
            self._dict.update(super().__dict__())

        return self._dict
