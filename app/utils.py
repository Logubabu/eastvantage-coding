import math
from typing import Tuple

EARTH_RADIUS_KM = 6371.0088

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth
    using the Haversine formula.
    
    Args:
        lat1: Latitude of the first point in degrees.
        lon1: Longitude of the first point in degrees.
        lat2: Latitude of the second point in degrees.
        lon2: Longitude of the second point in degrees.
        
    Returns:
        The distance between the two points in kilometers.
    """
    # Convert latitude and longitude from degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = (
        math.sin(delta_phi / 2.0) ** 2 +
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    return EARTH_RADIUS_KM * c

def get_bounding_box(latitude: float, longitude: float, distance_km: float) -> Tuple[float, float, float, float]:
    """Calculate the bounding box coordinates (min_lat, max_lat, min_lon, max_lon)
    for a given center coordinate and radius.
    
    This is used to optimize spatial queries in database systems that do not
    have native spatial support (like standard SQLite).
    
    Args:
        latitude: Latitude of the center point in degrees.
        longitude: Longitude of the center point in degrees.
        distance_km: Search radius in kilometers.
        
    Returns:
        A tuple of (min_lat, max_lat, min_lon, max_lon).
    """
    # Angular distance in radians
    angular_distance = distance_km / EARTH_RADIUS_KM
    
    lat_rad = math.radians(latitude)
    lon_rad = math.radians(longitude)
    
    # Calculate min and max latitude
    min_lat_rad = lat_rad - angular_distance
    max_lat_rad = lat_rad + angular_distance
    
    min_lat = math.degrees(min_lat_rad)
    max_lat = math.degrees(max_lat_rad)
    
    # Handle poles wrapping
    if min_lat > -90.0 and max_lat < 90.0:
        # Calculate delta longitude
        # Since longitude lines converge towards the poles, we adjust for latitude
        lat_cos = math.cos(lat_rad)
        if lat_cos > 0.0001:  # Avoid division by zero close to poles
            delta_lon_rad = math.asin(math.sin(angular_distance) / lat_cos)
            delta_lon = math.degrees(delta_lon_rad)
            min_lon = longitude - delta_lon
            max_lon = longitude + delta_lon
        else:
            # Very close to poles, search the entire longitude range
            min_lon = -180.0
            max_lon = 180.0
    else:
        # Bounding box includes a pole, search the entire longitude range
        min_lat = max(min_lat, -90.0)
        max_lat = min(max_lat, 90.0)
        min_lon = -180.0
        max_lon = 180.0

    # Ensure coordinates stay within geographical limits
    min_lat = max(min_lat, -90.0)
    max_lat = min(max_lat, 90.0)
    
    # If the longitude wraps around, we return -180 and 180 for standard SQLite BETWEEN queries
    # to avoid complex wrap-around logic in simple SQL. This is safe and covers all points.
    if min_lon < -180.0 or max_lon > 180.0:
        min_lon = -180.0
        max_lon = 180.0
        
    return min_lat, max_lat, min_lon, max_lon
