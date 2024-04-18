import os

import requests
from fastapi import Request
from stat_fastapi.exceptions import NotFoundException
from stat_fastapi.models.opportunity import (
    Opportunity,
    OpportunityRequest,
)
from stat_fastapi.models.order import Order
from stat_fastapi.models.product import Product, Provider, ProviderRole

from stat_fastapi_planet.models import Constraints
from stat_fastapi_planet.settings import Settings

PLANET_BASE_URL = "https://oden.prod.planet-labs.com/v2"


PRODUCTS = [
    Product(
        id="PL-123456:Assured Tasking",
        description="SkySat Assured Tasking ",
        license="proprietary",
        providers=[
            Provider(
                name="Planet",
                roles=[
                    ProviderRole.licensor,
                    ProviderRole.producer,
                    ProviderRole.processor,
                    ProviderRole.host,
                ],
                url="https://www.planet.com/",
            )
        ],
        parameters=Constraints,
        links=[],
    ),
    Product(
        id="PL-123456:Flexible Tasking",
        description="SkySat Flexible Tasking ",
        license="proprietary",
        providers=[
            Provider(
                name="Planet",
                roles=[
                    ProviderRole.licensor,
                    ProviderRole.producer,
                    ProviderRole.processor,
                    ProviderRole.host,
                ],
                url="https://www.planet.com/",
            )
        ],
        parameters=Constraints,
        links=[],
    ),
]


def stat_to_opportunities_request(search: OpportunityRequest):
    """
    :param search: STAC search as passed on to find_future_items
    :return: a triple of iw request body, geom and bbox (geom and bbox needed again later to construct STAC answers)
    """
    pl_number, pl_product = search.product_id.split(":")

    return {
        "item": {
            "name": "Planet_Request",
            "description": "STAT Sprint 3",
            "timeframe": {
                "lowerBoundType": "CLOSED",
                "lowerEndpoint": search.datetime[0].isoformat(),
                "upperBoundType": "CLOSED",
                "upperEndpoint": search.datetime[1].isoformat(),
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                    search.geometry.model_dump()["coordinates"][0],
                    search.geometry.model_dump()["coordinates"][1],
                    0,
                ],
            },
            "offeringId": "391327b7-f4ee-4e7f-a894-3cffef19cae0",
            "frequency": "ONCE",
            "offeringParamValues": {"priority": "STANDARD", "sensor": "blacksky"},
            "externalId": "1234",
        },
    }


def get_opportunities(planet_request: dict, token: str):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "authorization": token,
    }

    scheduling_type = planet_request.constraints.get('scheduling_type')
    match (scheduling_type):
        case 'Assured':
            return find_assured_opportunities(search_request)
        case 'Flexible':
            return find_flexible_opportunities(search_request)

    raise NotImplementedError(f"Unsupported scheduling type: {scheduling_type}")

    r = requests.post(
        f"{PLANET_BASE_URL}/feasibility/plan", headers=headers, json=planet_request
    )
    return r.json()["opportunities"]


def planet_opportunity_to_opportunity(iw: dict):
    """
    translates a Planet Imaging Windows into a STAT opportunity
    :param iw: an element from the 'imaging_windows' array of a /imaging_windows/[search_id] response
    :return: a corresponding STAT opportunity
    """

    opportunity = Opportunity(
        id=iw["satellite"],
        geometry={"type": "Point", "coordinates": [iw["longitude"], iw["latitude"], 0]},
        properties=dict(
            product_id="BS-Test:Standard",
            datetime=f"{iw['timestamp']}/{iw['timestamp']}",
            off_nadir=iw["offNadirAngleDegrees"],
        ),
    )

    return opportunity


class StatPlanetBackend:

    def __init__(self):
        self.settings = Settings.load()

    def products(self, request: Request) -> list[Product]:
        """
        Return a list of supported products.
        """
        return PRODUCTS

    def product(self, product_id: str, request: Request) -> Product | None:
        """
        Return the product identified by `product_id` or `None` if it isn't
        supported.
        """
        try:
            return next((product for product in PRODUCTS if product.id == product_id))
        except StopIteration as exc:
            raise NotFoundException() from exc

    async def search_opportunities(
        self, search: OpportunityRequest, request: Request
    ) -> list[Opportunity]:
        """
        Search for ordering opportunities for the given search parameters.
        """
        token = os.environ.get("BACKEND_TOKEN")
        if authorization := request.headers.get("authorization"):
            token = authorization.replace("Bearer ", "")
        planet_request = stat_to_opportunities_request(search)
        opportunities = get_opportunities(planet_request, token)
        return [planet_opportunity_to_opportunity(iw) for iw in opportunities]

    async def create_order(self, search: OpportunityRequest, request: Request) -> Order:
        """
        Create a new order.
        """
        raise NotImplementedError()

    async def get_order(self, order_id: str, request: Request):
        """
        Show details for order with `order_id`.
        """
        raise NotImplementedError()
