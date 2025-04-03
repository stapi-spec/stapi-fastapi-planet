from fastapi import FastAPI

from planet.backends import (
    create_order,
    get_order,
    mock_get_order_statuses,
    mock_get_orders,
    search_opportunities,
)
from planet.models import (
    PlanetOpportunityProperties,
    PlanetOrderParameters,
    PlanetProductConstraints,
    provider_planet,
)
from planet.settings import Settings
from stapi_fastapi import Product
from stapi_fastapi.models.conformance import CORE, OPPORTUNITIES
from stapi_fastapi.routers.root_router import RootRouter

pl_number = {"production": "INT-003001", "staging": "INT-004004"}[Settings().env]

product_test_planet_sync_opportunity = Product(
    id=f"{pl_number}:Assured Tasking",
    title=f"{pl_number}:Assured Tasking",
    description="Assured SkySat Tasking",
    license="proprietary",
    keywords=["satellite", "provider"],
    providers=[provider_planet],
    create_order=create_order,
    search_opportunities=search_opportunities,
    search_opportunities_async=None,
    get_opportunity_collection=None,
    constraints=PlanetProductConstraints,
    opportunity_properties=PlanetOpportunityProperties,
    order_parameters=PlanetOrderParameters,
)

# PlanetRootRouter
# get_products=get_products,
root_router = RootRouter(
    get_orders=mock_get_orders,
    get_order=get_order,
    get_order_statuses=mock_get_order_statuses,
    # get_opportunity_search_records=None,
    # get_opportunity_search_record=None,
    conformances=[CORE, OPPORTUNITIES],  # , ASYNC_OPPORTUNITIES
)
root_router.add_product(product_test_planet_sync_opportunity)

app: FastAPI = FastAPI()
app.include_router(root_router, prefix="")
