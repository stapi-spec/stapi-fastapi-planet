from datetime import datetime, timezone

from planet.models import (
    OffNadirAngleRange,
    PlanetOpportunityProperties,
    PlanetOrderParameters,
    PlanetSatelliteType,
)
from stapi_fastapi import Link, Product
from stapi_fastapi.constants import TYPE_JSON
from stapi_fastapi.models.opportunity import (
    Opportunity,
    OpportunityPayload,
)
from stapi_fastapi.models.order import (
    Order,
    OrderPayload,
    OrderProperties,
    OrderSearchParameters,
    OrderStatus,
    OrderStatusCode,
)

ORDER_FIELDS_TO_PROPERTIES = [
    "pl_number",
    "satelite_types",
    "name",
    "scheduling_type",
    # TODO finalize fields to be copied (or copy everything we receive except fields used elsewhere?)
]

PLANET_ORDER_TO_STAPI_ORDER_STATUS = {
    "RECEIVED": OrderStatusCode.received,
    "PENDING": OrderStatusCode.scheduled,
    "IN_PROGRESS": OrderStatusCode.scheduled,
    "FULFILLED": OrderStatusCode.completed,
    "CANCELLED": OrderStatusCode.canceled,
    "REJECTED": OrderStatusCode.rejected,
    "REQUESTED": OrderStatusCode.received,
    "FINALIZING": OrderStatusCode.processing,
    "PENDING_CANCELLATION": OrderStatusCode.user_canceled,
    "EXPIRED": OrderStatusCode.expired,
    "FAILED": OrderStatusCode.failed,
}


def planet_order_status_to_stapi_order_status(planet_status: str) -> OrderStatus:
    return OrderStatus(
        timestamp=datetime.now(tz=timezone.utc),
        status_code=PLANET_ORDER_TO_STAPI_ORDER_STATUS.get(
            planet_status, OrderStatusCode.held
        ),
    )


def planet_order_to_stapi_order(planet_order: dict) -> Order:
    """Convert the payload of a Planet tasking Order into a STAPI Order"""

    search_parameters = OrderSearchParameters(
        datetime=(planet_order["start_time"], planet_order["end_time"]),
        geometry=planet_order["original_geometry"],
    )

    opportunity_properties = {"imaging_window": planet_order["imaging_window"]}
    order_parameters = {
        key: planet_order[key]
        for key in ORDER_FIELDS_TO_PROPERTIES
        if key in planet_order
    }

    return Order(
        id=planet_order["id"],
        geometry=planet_order["geometry"],
        properties=OrderProperties(
            product_id=planet_order.get("product", ""),
            created=planet_order["created_time"],
            status=planet_order_status_to_stapi_order_status(planet_order["status"]),
            search_parameters=search_parameters,
            opportunity_properties=opportunity_properties,
            order_parameters=order_parameters,
        ),
    )


def stapi_opportunity_payload_to_planet_iw_search(
    product: Product, search: OpportunityPayload
) -> dict:
    """Convert the opportunity search payload from STAPI to a Planet Imaging Window Search request"""

    pl_number, pl_product = product.id.split(":")

    return {
        "datetime": f"{search.datetime[0].isoformat()}/{search.datetime[1].isoformat()}",
        "pl_number": pl_number,
        "product": pl_product,
        "geometry": search.geometry.dict(),
    }


def planet_iw_to_stapi_order_payload(
    iw: dict, product: Product, search: OpportunityPayload
) -> OrderPayload:
    """Creating an order so it can be put into a create-order link"""

    return OrderPayload(
        datetime=(
            datetime.fromisoformat(iw["start_time"]),
            datetime.fromisoformat(iw["end_time"]),
        ),
        geometry=search.geometry,
        order_parameters=PlanetOrderParameters(
            imaging_window_id=iw["id"],
            name=f"{iw['start_time']} at {str(search.geometry.model_dump()['coordinates'])}",
        ),
    )


def planet_iw_to_stapi_opportunity(
    iw: dict, product: Product, search: OpportunityPayload, create_href: str
) -> Opportunity:
    cloud_forecast = 0
    if "cloud_forecast" in iw and len(cf := iw["cloud_forecast"]) > 0:
        cloud_forecast = cf[0].get("prediction")

    properties = PlanetOpportunityProperties(
        product_id=product.id,
        datetime=(iw["start_time"], iw["end_time"]),
        off_nadir_angle=OffNadirAngleRange(
            minimum=iw["off_nadir_angle_min"], maximum=iw["off_nadir_angle_max"]
        ),
        satellite_type=PlanetSatelliteType(iw["satellite_type"]),
        cloud_forecast=cloud_forecast,
    )

    create_order_body = planet_iw_to_stapi_order_payload(iw, product, search)

    links = [
        Link(
            href=create_href,
            rel="self",
            type=TYPE_JSON,
            title="create-order",
            method="POST",
            body=create_order_body,
        )
    ]

    return Opportunity(
        id=iw["id"],
        type="Feature",
        geometry=search.geometry,
        properties=properties,
        links=links,
    )


def planet_product_to_stapi_product(planet_product: dict, **router_args) -> Product:
    return Product(
        id=f"{planet_product['pl_number']}:{planet_product['product']}",
        title=planet_product["product"],
        description=planet_product["product"],
        license="proprietary",
        keywords=["satellite"],
        **router_args,
    )


def stapi_order_payload_to_planet_create_order_payload(
    payload: OrderPayload[PlanetOrderParameters], product: Product
) -> dict:
    pl_number, pl_product = product.id.split(":")
    return {
        "pl_number": pl_number,  # TODO if not single-contract
        "product": pl_product,  # TODO if not single-contract
        "imaging_window": payload.order_parameters.imaging_window_id,  # TODO if assured
        # TODO how to cast order parameters to _our_ order parameters here?
        "geometry": payload.geometry.model_dump(exclude={"bbox"}),
        "name": payload.order_parameters.name,
        # TODO: Add datetime if not assured
        # TODO: All the other things we might want to add
    }
