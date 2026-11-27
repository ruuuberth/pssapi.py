import datetime

import pytest

import pssapi


SHIP_DESIGN_NAME: str = "Oumaumau Progenitor Extended"
USER_ID: int = 4510693  # The worst.
# ListShipLayouts only returns the layouts of a ship owned by the access
# token's owner, so this test must be recorded with the ship id of the
# account paired to PSS_ACCESS_TOKEN.
SHIP_LAYOUTS_SHIP_ID: int = 8761013


@pytest.mark.asyncio
@pytest.mark.usefixtures("access_token", "client")
@pytest.mark.vcr(record_mode="once")
async def test_list_ship_layouts(access_token: str, client: pssapi.PssApiClient):
    ship_layouts = await client.ship_service.list_ship_layouts(access_token, SHIP_LAYOUTS_SHIP_ID)
    assert isinstance(ship_layouts, list)
    assert len(ship_layouts) > 0
    assert isinstance(ship_layouts[0], pssapi.entities.ShipLayout)
    ship_layout = ship_layouts[0]
    assert ship_layout.ship_layout_id >= 0
    assert ship_layout.ship_id == SHIP_LAYOUTS_SHIP_ID
    assert ship_layout.ship_layout_name is not None
    assert ship_layout.ship_layout_type is not None
    assert isinstance(ship_layout.has_lab_room, bool)


@pytest.mark.asyncio
@pytest.mark.usefixtures("access_token", "client", "client_date_time")
@pytest.mark.vcr(record_mode="once")
async def test_get_ship_by_user_id(access_token: str, client: pssapi.PssApiClient, client_date_time: str):
    ship = await client.ship_service.get_ship_by_user_id(access_token, client_date_time, USER_ID)
    assert isinstance(ship, pssapi.entities.Ship)


@pytest.mark.asyncio
@pytest.mark.usefixtures("access_token", "client")
@pytest.mark.vcr(record_mode="once")
async def test_inspect_ship(access_token: str, client: pssapi.PssApiClient):
    inspect_ship = await client.ship_service.inspect_ship(access_token, USER_ID)
    assert isinstance(inspect_ship, tuple)
    assert len(inspect_ship) == 2
    assert isinstance(inspect_ship[0], pssapi.entities.Ship)
    assert isinstance(inspect_ship[1], pssapi.entities.User)


@pytest.mark.asyncio
@pytest.mark.usefixtures("client", "client_date_time")
@pytest.mark.vcr()
async def test_list_all_ship_designs(client: pssapi.PssApiClient, client_date_time: datetime.datetime):
    ship_designs = await client.ship_service.list_all_ship_designs(client_date_time)
    assert isinstance(ship_designs, list)
    assert len(ship_designs) > 0
    assert isinstance(ship_designs[0], pssapi.entities.ShipDesign)


@pytest.mark.asyncio
@pytest.mark.usefixtures("client", "client_date_time")
@pytest.mark.vcr()
async def test_to_ship(client: pssapi.PssApiClient, client_date_time: datetime.datetime):
    ship_designs = await client.ship_service.to_ship(SHIP_DESIGN_NAME, client_date_time)
    assert isinstance(ship_designs, list)
    assert len(ship_designs) == 1
    assert isinstance(ship_designs[0], pssapi.entities.ShipDesign)
    assert ship_designs[0].ship_design_name == SHIP_DESIGN_NAME
