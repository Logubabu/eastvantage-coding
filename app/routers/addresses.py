import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/addresses",
    tags=["addresses"]
)

@router.get(
    "/search",
    response_model=List[schemas.AddressDistanceResponse],
    summary="Search addresses within a distance",
    description="Retrieve addresses that are within a specified distance (in kilometers) from a given coordinate."
)
def search_addresses(
    latitude: float = Query(
        ...,
        ge=-90.0,
        le=90.0,
        description="Center latitude",
        examples=[37.42202]
    ),
    longitude: float = Query(
        ...,
        ge=-180.0,
        le=180.0,
        description="Center longitude",
        examples=[-122.08408]
    ),
    radius_km: float = Query(
        ...,
        gt=0.0,
        description="Search radius in kilometers",
        examples=[5.0]
    ),
    db: Session = Depends(get_db)
):
    """Retrieve addresses within a given distance of specific coordinates."""
    logger.info("Search requested: lat=%s, lon=%s, radius=%s km", latitude, longitude, radius_km)
    
    results = crud.search_addresses_in_radius(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km
    )
    
    # Map the (Address, distance_km) tuple to the AddressDistanceResponse schema
    response_data = []
    for address, dist in results:
        # Convert SQLAlchemy object to dictionary and add distance_km
        addr_dict = schemas.AddressResponse.model_validate(address).model_dump()
        addr_dict["distance_km"] = round(dist, 4)
        response_data.append(schemas.AddressDistanceResponse(**addr_dict))
        
    return response_data

@router.post(
    "/",
    response_model=schemas.AddressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new address",
    description="Add a new address along with its coordinates to the address book."
)
def create_new_address(
    address: schemas.AddressCreate,
    db: Session = Depends(get_db)
):
    """Create a new address in the database."""
    return crud.create_address(db=db, address=address)

@router.get(
    "/",
    response_model=List[schemas.AddressResponse],
    summary="List addresses",
    description="Retrieve a paginated list of addresses from the address book."
)
def list_addresses(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    db: Session = Depends(get_db)
):
    """List addresses with pagination."""
    return crud.get_addresses(db=db, skip=skip, limit=limit)

@router.get(
    "/{address_id}",
    response_model=schemas.AddressResponse,
    summary="Get an address",
    description="Retrieve details of a specific address by its ID."
)
def read_address(
    address_id: int,
    db: Session = Depends(get_db)
):
    """Retrieve details of a specific address by its ID."""
    db_address = crud.get_address(db=db, address_id=address_id)
    if not db_address:
        logger.warning("Read failed: Address ID %d not found", address_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Address with ID {address_id} not found"
        )
    return db_address

@router.put(
    "/{address_id}",
    response_model=schemas.AddressResponse,
    summary="Update an address",
    description="Update fields of an existing address. Only provided fields are updated."
)
def update_existing_address(
    address_id: int,
    address_update: schemas.AddressUpdate,
    db: Session = Depends(get_db)
):
    """Update fields of an existing address."""
    db_address = crud.update_address(
        db=db,
        address_id=address_id,
        address_update=address_update
    )
    if not db_address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Address with ID {address_id} not found"
        )
    return db_address

@router.delete(
    "/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an address",
    description="Remove an address from the address book."
)
def delete_existing_address(
    address_id: int,
    db: Session = Depends(get_db)
):
    """Delete an address from the database."""
    success = crud.delete_address(db=db, address_id=address_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Address with ID {address_id} not found"
        )
    return
