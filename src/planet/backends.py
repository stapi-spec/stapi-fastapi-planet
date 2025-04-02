import logging

from fastapi import Request
from returns.maybe import Maybe, Nothing, Some
from returns.result import Failure, ResultE, Success

from stapi_fastapi import Link
from stapi_fastapi.constants import TYPE_JSON
from stapi_fastapi.models.opportunity import (
    Opportunity,
    OpportunityPayload,
)
from stapi_fastapi.models.order import (
    Order,
    OrderPayload,
    OrderStatus,
)
from stapi_fastapi.models.product import ProductsCollection
from stapi_fastapi.routers.product_router import ProductRouter
from stapi_fastapi.routers.route_names import CREATE_ORDER, LIST_PRODUCTS

from . import conversions
from .client import Client

logger = logging.getLogger(__name__)


async def mock_get_orders(
    next: str | None, limit: int, request: Request
) -> ResultE[tuple[list[Order], Maybe[str]]]:
    """
    Return orders from backend.  Handle pagination/limit if applicable
    """
    try:
        start = 0
        limit = min(limit, 100)

        order_ids = [*request.state._orders_db._orders.keys()]

        if next:
            start = order_ids.index(next)
        end = start + limit
        ids = order_ids[start:end]
        orders = [request.state._orders_db.get_order(order_id) for order_id in ids]

        if end > 0 and end < len(order_ids):
            return Success(
                (orders, Some(request.state._orders_db._orders[order_ids[end]].id))
            )
        return Success((orders, Nothing))
    except Exception as e:
        return Failure(e)


async def get_order(order_id: str, request: Request) -> ResultE[Maybe[Order]]:
    """
    Show details for order with `order_id`.
    """
    try:
        return Success(
            Maybe.from_optional(
                conversions.planet_order_to_stapi_order(
                    Client(request).get_order(order_id)
                )
            )
        )
    except Exception as e:
        return Failure(e)


async def mock_get_order_statuses(
    order_id: str, next: str | None, limit: int, request: Request
) -> ResultE[Maybe[tuple[list[OrderStatus], Maybe[str]]]]:
    try:
        start = 0
        limit = min(limit, 100)
        statuses = request.state._orders_db.get_order_statuses(order_id)
        if statuses is None:
            return Success(Nothing)

        if next:
            start = int(next)
        end = start + limit
        stati = statuses[start:end]

        if end > 0 and end < len(statuses):
            return Success(Some((stati, Some(str(end)))))
        return Success(Some((stati, Nothing)))
    except Exception as e:
        return Failure(e)


async def get_products(self, request: Request, **router_args) -> ProductsCollection:
    links = [
        Link(
            href=str(request.url_for(f"{self.name}:{LIST_PRODUCTS}")),
            rel="self",
            type=TYPE_JSON,
        ),
    ]
    return ProductsCollection(
        products=[
            conversions.planet_product_to_stapi_product(planet_product, **router_args)
            for planet_product in Client(request).get_products()
        ],
        links=links,
    )


async def create_order(
    product_router: ProductRouter, payload: OrderPayload, request: Request
) -> ResultE[Order]:
    try:
        planet_payload = conversions.stapi_order_payload_to_planet_create_order_payload(
            payload, product_router.product
        )
        planet_order_response = Client(request).create_order(planet_payload)
        stapi_order = conversions.planet_order_to_stapi_order(planet_order_response)
        return Success(stapi_order)
    except Exception as e:
        return Failure(e)


# TODO why does this return a list of Opportunities and not an OpportunityCollection?
#      and what does the related "get_search_opportunities" do in comparison?
async def search_opportunities(
    product_router: ProductRouter,
    search: OpportunityPayload,
    next: str | None,
    limit: int,
    request: Request,
) -> ResultE[tuple[list[Opportunity], Maybe[str]]]:
    try:
        iw_request = conversions.stapi_opportunity_payload_to_planet_iw_search(
            product_router.product, search
        )
        imaging_windows = Client(request).get_imaging_windows(iw_request)
        create_order_name = f"{product_router.root_router.name}:{product_router.product.id}:{CREATE_ORDER}"
        create_href = str(request.url_for(create_order_name))

        opportunities = [
            conversions.planet_iw_to_stapi_opportunity(
                iw, product_router.product, search, create_href
            )
            for iw in imaging_windows
        ]
        # return OpportunityCollection(features=opportunities)
        return Success((opportunities, Nothing))
    except Exception as e:
        return Failure(e)
