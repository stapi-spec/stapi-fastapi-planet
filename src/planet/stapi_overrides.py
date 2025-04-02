from fastapi import Request

from planet.backends import create_order, search_opportunities
from planet.models import (
    PlanetOpportunityProperties,
    PlanetOrderParameters,
    PlanetProductConstraints,
)
from stapi_fastapi.models.product import ProductsCollection
from stapi_fastapi.routers import RootRouter


# TODO this gets products from the API instead of hard-coded, but we also need to create routers dynamically
#   we could do this relatively easy by replacing the individual routers with a catch-all product router,
#   but it appears the ProductRouters carry a lot of context beyond the pure routing
class PlanetRootRouter(RootRouter):
    def __init__(self, get_products, *args, **kwargs):
        self._get_products = get_products
        super().__init__(*args, **kwargs)

    def get_products(
        self, request: Request, next: str | None = None, limit: int = 10
    ) -> ProductsCollection:
        return self._get_products(
            request,
            create_order=create_order,
            search_opportunities=search_opportunities,
            search_opportunities_async=None,
            get_opportunity_collection=None,
            constraints=PlanetProductConstraints,
            opportunity_properties=PlanetOpportunityProperties,
            order_parameters=PlanetOrderParameters,
        )
