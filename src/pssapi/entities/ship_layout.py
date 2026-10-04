from ..types import EntityInfo as _EntityInfo
from .entity_base import EntityBase as _EntityBase
from .raw import ShipLayoutRaw as _ShipLayoutRaw


class ShipLayout(_ShipLayoutRaw, _EntityBase):
    def __init__(self, ship_layout_info: _EntityInfo) -> None:
        super().__init__(ship_layout_info)
