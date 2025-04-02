from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Self
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
from geojson_pydantic import Point
from geojson_pydantic.types import Position2D
from httpx import Response
from pydantic import BaseModel, Field, model_validator
from pytest import fail

from stapi_fastapi.models.opportunity import (
    Opportunity,
    OpportunityCollection,
    OpportunityProperties,
    OpportunitySearchRecord,
)
from stapi_fastapi.models.order import (
    Order,
    OrderParameters,
    OrderStatus,
)
from stapi_fastapi.models.product import (
    Product,
    Provider,
    ProviderRole,
)

from backends import (
    mock_create_order,
    mock_get_opportunity_collection,
    search_opportunities,
    mock_search_opportunities_async,
)

type link_dict = dict[str, Any]


def find_link(links: list[link_dict], rel: str) -> link_dict | None:
    return next((link for link in links if link["rel"] == rel), None)



class InMemoryOrderDB:
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._statuses: dict[str, list[OrderStatus]] = defaultdict(list)

    def get_order(self, order_id: str) -> Order | None:
        return deepcopy(self._orders.get(order_id))

    def get_orders(self) -> list[Order]:
        return deepcopy(list(self._orders.values()))

    def put_order(self, order: Order) -> None:
        self._orders[order.id] = deepcopy(order)

    def get_order_statuses(self, order_id: str) -> list[OrderStatus] | None:
        return deepcopy(self._statuses.get(order_id))

    def put_order_status(self, order_id: str, status: OrderStatus) -> None:
        self._statuses[order_id].append(deepcopy(status))


class InMemoryOpportunityDB:
    def __init__(self) -> None:
        self._search_records: dict[str, OpportunitySearchRecord] = {}
        self._collections: dict[str, OpportunityCollection] = {}

    def get_search_record(self, search_id: str) -> OpportunitySearchRecord | None:
        return deepcopy(self._search_records.get(search_id))

    def get_search_records(self) -> list[OpportunitySearchRecord]:
        return deepcopy(list(self._search_records.values()))

    def put_search_record(self, search_record: OpportunitySearchRecord) -> None:
        self._search_records[search_record.id] = deepcopy(search_record)

    def get_opportunity_collection(self, collection_id) -> OpportunityCollection | None:
        return deepcopy(self._collections.get(collection_id))

    def put_opportunity_collection(self, collection: OpportunityCollection) -> None:
        if collection.id is None:
            raise ValueError("collection must have an id")
        self._collections[collection.id] = deepcopy(collection)



class MyProductConstraints(BaseModel):
    off_nadir: int


class OffNadirRange(BaseModel):
    minimum: int = Field(ge=0, le=45)
    maximum: int = Field(ge=0, le=45)

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.minimum > self.maximum:
            raise ValueError("range minimum cannot be greater than maximum")
        return self


class MyOpportunityProperties(OpportunityProperties):
    off_nadir: OffNadirRange
    vehicle_id: list[Literal[1, 2, 5, 7, 8]]
    platform: Literal["platform_id"]


class MyOrderParameters(OrderParameters):
    s3_path: str | None = None


provider_planet = Provider(
    name="Planet",
    description="A provider for Test data",
    roles=[ProviderRole.producer],  # Example role
    url="https://www.planet.com",  # Must be a valid URL
)


product_test_planet_sync_opportunity = Product(
    id="INT-003001:Assured Tasking",
    title="Assured Tasking",
    description="Assured SkySat Tasking",
    license="proprietary",
    keywords=["satellite", "provider"],
    providers=[provider_planet],
    links=[],
    create_order=mock_create_order,
    search_opportunities=search_opportunities,
    search_opportunities_async=None,
    get_opportunity_collection=None,
    constraints=MyProductConstraints,
    opportunity_properties=MyOpportunityProperties,
    order_parameters=MyOrderParameters,
)


def create_mock_opportunity() -> Opportunity:
    now = datetime.now(timezone.utc)  # Use timezone-aware datetime
    start = now
    end = start + timedelta(days=5)

    # Create a list of mock opportunities for the given product
    return Opportunity(
        id=str(uuid4()),
        type="Feature",
        geometry=Point(
            type="Point",
            coordinates=Position2D(longitude=0.0, latitude=0.0),
        ),
        properties=MyOpportunityProperties(
            product_id="xyz123",
            datetime=(start, end),
            off_nadir=OffNadirRange(minimum=20, maximum=22),
            vehicle_id=[1],
            platform="platform_id",
            other_thing="abcd1234",  # type: ignore
        ),
    )
