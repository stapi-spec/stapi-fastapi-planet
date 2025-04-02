from datetime import datetime, timezone

from pydantic import AwareDatetime

from planet.models import PlanetOpportunityProperties, OffNadirAngleRange, PlanetSatelliteType
from stapi_fastapi import Product
from stapi_fastapi.models.order import Order, OrderProperties, OrderSearchParameters, OrderStatus, OrderStatusCode
from stapi_fastapi.models.opportunity import (
    Opportunity,
    OpportunityCollection,
    OpportunityPayload,
    OpportunitySearchRecord,
    OpportunitySearchStatus,
    OpportunitySearchStatusCode,
)

ORDER_FIELDS_TO_PROPERTIES = [
    'pl_number',
    'satelite_types',
    'name',
    'scheduling_type',
    # TODO finalize fields to be copied (or copy everything we receive except fields used elsewhere?)
]

PLANET_ORDER_TO_STAPI_ORDER_STATUS = {
    'RECEIVED': OrderStatusCode.received,
    'PENDING': OrderStatusCode.pending,
    'IN_PROGRESS': OrderStatusCode.in_progress,
    'FULFILLED': OrderStatusCode.completed,
    'PENDING_CANCELLATION' : OrderStatusCode.pending_cancellation,
    'CANCELLED': OrderStatusCode.canceled,
    'EXPIRED': OrderStatusCode.expired,
    'REJECTED': OrderStatusCode.rejected,
    'REQUESTED': OrderStatusCode.requested,
    'FINALIZING': OrderStatusCode.processing,
    'FAILED': OrderStatusCode.failed
}


def planet_order_status_to_stapi_order_status(planet_status: str) -> OrderStatus:

    return OrderStatus(
        timestamp=datetime.now(tz=timezone.utc),
        status_code=PLANET_ORDER_TO_STAPI_ORDER_STATUS.get(planet_status, OrderStatusCode.held)
    )


def planet_order_to_stapi_order(planet_order: dict) -> Order:
    """Convert the payload of a Planet tasking Order into a STAPI Order"""

    search_parameters = OrderSearchParameters(
        datetime=(planet_order["start_time"], planet_order["end_time"]),
        geometry=planet_order["original_geometry"]
    )

    opportunity_properties = {
        'imaging_window': planet_order['imaging_window']
    }
    order_parameters = {key:planet_order[key] for key in ORDER_FIELDS_TO_PROPERTIES if key in planet_order}

    return Order(
        id=planet_order["id"],
        geometry=planet_order["geometry"],
        properties=OrderProperties(
            product_id=planet_order.get("product", ""),
            created=planet_order["created_time"],
            status=planet_order_status_to_stapi_order_status(planet_order["status"]),
            search_parameters=search_parameters,
            opportunity_properties=opportunity_properties,
            order_parameters=order_parameters
        )
    )

def stapi_opportunity_payload_to_planet_iw_search(product: Product, search: OpportunityPayload) -> dict:
    """Convert the opportunity search payload from STAPI to a Planet Imaging Window Search request"""

    pl_number, pl_product = product.id.split(':')

    return {
        "datetime": f"{search.datetime[0].isoformat()}/{search.datetime[1].isoformat()}",
        "pl_number": pl_number,
        "product": pl_product,
        "geometry": search.geometry.dict(),
    }

def planet_iw_to_stapi_opportunity(iw: dict, product: Product, search: OpportunityPayload) -> Opportunity:

    print(iw)

    properties = PlanetOpportunityProperties(
        product_id=product.id,
        datetime=(iw['start_time'], iw['end_time']),
        off_nadir_angle=OffNadirAngleRange(
            minimum=iw['off_nadir_angle_min'],
            maximum=iw['off_nadir_angle_max']),
        satellite_type=PlanetSatelliteType(iw['satellite_type']),
        title='Planet Assured Imaging Window @ ' + iw['start_time'],
    )
    if 'cloud_forecast' in iw and len(cf := iw['cloud_forecast']) > 0:
        properties.cloud_forecast = cf[0].get('prediction')

    return Opportunity(
        id=iw["id"],
        type="Feature",
        geometry=search.geometry,
        properties=properties
    )
