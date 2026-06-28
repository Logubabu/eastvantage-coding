import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app import models, schemas
from app.utils import get_bounding_box, haversine_distance

logger = logging.getLogger(__name__)

def get_address(db: Session, address_id: int) -> Optional[models.Address]:
    """Retrieve an address by its ID.
    
    Args:
        db: The database session.
        address_id: The ID of the address to retrieve.
        
    Returns:
        The Address model object if found, else None.
    """
    logger.debug("Fetching address with ID: %d", address_id)
    return db.query(models.Address).filter(models.Address.id == address_id).first()

def get_addresses(db: Session, skip: int = 0, limit: int = 100) -> List[models.Address]:
    """Retrieve a list of addresses with pagination.
    
    Args:
        db: The database session.
        skip: The number of addresses to skip.
        limit: The maximum number of addresses to return.
        
    Returns:
        A list of Address model objects.
    """
    logger.debug("Fetching addresses skip=%d, limit=%d", skip, limit)
    return db.query(models.Address).offset(skip).limit(limit).all()

def create_address(db: Session, address: schemas.AddressCreate) -> models.Address:
    """Create a new address in the database.
    
    Args:
        db: The database session.
        address: The address data to create.
        
    Returns:
        The newly created Address model object.
    """
    logger.info("Creating new address: %s, %s", address.street, address.city)
    db_address = models.Address(
        street=address.street,
        city=address.city,
        state=address.state,
        country=address.country,
        postal_code=address.postal_code,
        latitude=address.latitude,
        longitude=address.longitude
    )
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    logger.info("Address created successfully with ID: %d", db_address.id)
    return db_address

def update_address(db: Session, address_id: int, address_update: schemas.AddressUpdate) -> Optional[models.Address]:
    """Update an existing address.
    
    Args:
        db: The database session.
        address_id: The ID of the address to update.
        address_update: The updated fields.
        
    Returns:
        The updated Address model object if found, else None.
    """
    logger.info("Updating address ID: %d", address_id)
    db_address = get_address(db, address_id)
    if not db_address:
        logger.warning("Address with ID %d not found for update", address_id)
        return None

    # Get only the fields that were explicitly set in the request
    update_data = address_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_address, key, value)

    db.commit()
    db.refresh(db_address)
    logger.info("Address ID %d updated successfully", address_id)
    return db_address

def delete_address(db: Session, address_id: int) -> bool:
    """Delete an address.
    
    Args:
        db: The database session.
        address_id: The ID of the address to delete.
        
    Returns:
        True if the address was found and deleted, else False.
    """
    logger.info("Deleting address ID: %d", address_id)
    db_address = get_address(db, address_id)
    if not db_address:
        logger.warning("Address with ID %d not found for deletion", address_id)
        return False
    
    db.delete(db_address)
    db.commit()
    logger.info("Address ID %d deleted successfully", address_id)
    return True

def search_addresses_in_radius(
    db: Session,
    latitude: float,
    longitude: float,
    radius_km: float
) -> List[Tuple[models.Address, float]]:
    """Retrieve addresses within a given distance of specific coordinates.
    
    This is highly optimized by first fetching database records within a bounding box
    (utilizing database indexes on latitude and longitude), and then calculating
    the precise Haversine distance in Python to filter and sort the final results.
    
    Args:
        db: The database session.
        latitude: The center latitude.
        longitude: The center longitude.
        radius_km: The maximum search radius in kilometers.
        
    Returns:
        A list of tuples, each containing (Address model, distance_km), sorted by distance.
    """
    logger.info(
        "Searching addresses within radius %s km of (%s, %s)",
        radius_km, latitude, longitude
    )
    
    # Calculate bounding box coordinates
    min_lat, max_lat, min_lon, max_lon = get_bounding_box(latitude, longitude, radius_km)
    
    # Query database using coordinates bounding box.
    # Because latitude and longitude columns are indexed, this is an index range scan (very fast).
    candidates = db.query(models.Address).filter(
        models.Address.latitude >= min_lat,
        models.Address.latitude <= max_lat,
        models.Address.longitude >= min_lon,
        models.Address.longitude <= max_lon
    ).all()
    
    logger.debug("Found %d candidate addresses in database bounding box", len(candidates))
    
    # Calculate exact Haversine distance and filter candidates
    results: List[Tuple[models.Address, float]] = []
    for address in candidates:
        dist = haversine_distance(latitude, longitude, address.latitude, address.longitude)
        if dist <= radius_km:
            results.append((address, dist))
            
    # Sort results by distance (closest first)
    results.sort(key=lambda x: x[1])
    logger.info("Found %d addresses within precise %s km radius", len(results), radius_km)
    
    return results
