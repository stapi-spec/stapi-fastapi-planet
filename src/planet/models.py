from enum import Enum
from typing import Self

from pydantic import BaseModel, Field, model_validator

from stapi_fastapi.models.opportunity import (
    OpportunityProperties,
)
from stapi_fastapi.models.order import (
    OrderParameters,
)
from stapi_fastapi.models.product import (
    Provider,
    ProviderRole,
)


class PlanetSatelliteType(str, Enum):
    SKYSAT = "SKYSAT"
    PELICAN = "PELICAN"
    TANAGER = "TANAGER"


class PlanetProductConstraints(BaseModel):
    off_nadir: float


class OffNadirAngleRange(BaseModel):
    minimum: float = Field(ge=0, le=90)
    maximum: float = Field(ge=0, le=90)

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.minimum > self.maximum:
            raise ValueError("range minimum cannot be greater than maximum")
        return self


class PlanetOpportunityProperties(OpportunityProperties):
    off_nadir_angle: OffNadirAngleRange
    satellite_type: PlanetSatelliteType
    cloud_forecast: float
    # off_nadir start/end
    # sat_elevation_angle
    # sat_azimuth_angle
    # sat_azimuth_angle start/end
    # sun_elevation_angle
    # solar_zenith_angle
    # low_light
    # ground_sample_distance
    # assured_tasking_tier
    # conflicting_orders
    # quota_priority_multiplier
    # sensitivity_mode


class PlanetOrderParameters(OrderParameters):
    imaging_window_id: str
    name: str


provider_planet = Provider(
    name="Planet",
    description="A provider for Test data",
    roles=[ProviderRole.producer],  # Example role
    url="https://www.planet.com",  # Must be a valid URL
)
