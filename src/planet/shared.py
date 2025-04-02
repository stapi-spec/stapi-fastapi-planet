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

from models import (
    PlanetProductConstraints,
    PlanetOpportunityProperties,
    PlanetOrderParameters,
    provider_planet
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
    constraints=PlanetProductConstraints,
    opportunity_properties=PlanetOpportunityProperties,
    order_parameters=PlanetOrderParameters,
)

