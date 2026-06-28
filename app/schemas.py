from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class AddressBase(BaseModel):
    """Base Pydantic model for address data validation."""
    street: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Street address (e.g. 1600 Amphitheatre Pkwy)",
        examples=["1600 Amphitheatre Pkwy"]
    )
    city: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="City name",
        examples=["Mountain View"]
    )
    state: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="State or Province",
        examples=["CA"]
    )
    country: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Country",
        examples=["United States"]
    )
    postal_code: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Postal or ZIP code",
        examples=["94043"]
    )
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude (-90.0 to 90.0)",
        examples=[37.42202]
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude (-180.0 to 180.0)",
        examples=[-122.08408]
    )

    @field_validator("street", "city", "state", "country", "postal_code")
    @classmethod
    def strip_whitespace_and_check_non_empty(cls, v: str) -> str:
        """Strip whitespace and check that the string is not empty after stripping."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or only whitespace")
        return stripped

class AddressCreate(AddressBase):
    """Schema for creating a new address."""
    pass

class AddressUpdate(BaseModel):
    """Schema for updating an existing address. All fields are optional."""
    street: Optional[str] = Field(None, min_length=1, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=1, max_length=100)
    country: Optional[str] = Field(None, min_length=1, max_length=100)
    postal_code: Optional[str] = Field(None, min_length=1, max_length=20)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)

    @field_validator("street", "city", "state", "country", "postal_code")
    @classmethod
    def strip_whitespace_and_check_non_empty_optional(cls, v: Optional[str]) -> Optional[str]:
        """Strip whitespace and check that the string is not empty if provided."""
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or only whitespace")
        return stripped

from pydantic import BaseModel, Field, field_validator, ConfigDict

class AddressResponse(AddressBase):
    """Schema for returning address data."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AddressDistanceResponse(AddressResponse):
    """Schema for returning address data along with calculated distance in km."""
    distance_km: float

    model_config = ConfigDict(from_attributes=True)
