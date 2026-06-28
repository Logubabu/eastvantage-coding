import pytest

def test_create_address_success(client):
    """Test creating a valid address successfully."""
    payload = {
        "street": "1600 Amphitheatre Pkwy",
        "city": "Mountain View",
        "state": "CA",
        "country": "United States",
        "postal_code": "94043",
        "latitude": 37.42202,
        "longitude": -122.08408
    }
    response = client.post("/api/v1/addresses/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["street"] == "1600 Amphitheatre Pkwy"
    assert data["city"] == "Mountain View"
    assert data["latitude"] == 37.42202
    assert data["longitude"] == -122.08408
    assert "created_at" in data
    assert "updated_at" in data

@pytest.mark.parametrize(
    "lat,lon,expected_error_loc",
    [
        (90.1, -122.0, "latitude"),
        (-90.1, -122.0, "latitude"),
        (37.4, 180.1, "longitude"),
        (37.4, -180.1, "longitude"),
    ]
)
def test_create_address_coordinates_validation(client, lat, lon, expected_error_loc):
    """Test that coordinates out of geographical range are rejected."""
    payload = {
        "street": "Test Street",
        "city": "Test City",
        "state": "TS",
        "country": "Test Country",
        "postal_code": "12345",
        "latitude": lat,
        "longitude": lon
    }
    response = client.post("/api/v1/addresses/", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(expected_error_loc in error["loc"] for error in errors)

@pytest.mark.parametrize(
    "field", ["street", "city", "state", "country", "postal_code"]
)
def test_create_address_empty_fields_validation(client, field):
    """Test that empty or whitespace-only fields are rejected."""
    payload = {
        "street": "1600 Amphitheatre Pkwy",
        "city": "Mountain View",
        "state": "CA",
        "country": "United States",
        "postal_code": "94043",
        "latitude": 37.4220,
        "longitude": -122.0841
    }
    # Test empty string
    payload[field] = ""
    response = client.post("/api/v1/addresses/", json=payload)
    assert response.status_code == 422
    
    # Test whitespace-only string
    payload[field] = "    "
    response2 = client.post("/api/v1/addresses/", json=payload)
    assert response2.status_code == 422

def test_get_address_not_found(client):
    """Test reading a non-existent address returns 404."""
    response = client.get("/api/v1/addresses/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Address with ID 99999 not found"

def test_crud_lifecycle_flow(client):
    """Test standard CRUD operations (Create, Read, Update, Delete) for an address."""
    # 1. Create
    payload = {
        "street": "Original Street",
        "city": "Original City",
        "state": "OS",
        "country": "Original Country",
        "postal_code": "00000",
        "latitude": 10.0,
        "longitude": 20.0
    }
    post_res = client.post("/api/v1/addresses/", json=payload)
    assert post_res.status_code == 201
    address_id = post_res.json()["id"]

    # 2. Read
    get_res = client.get(f"/api/v1/addresses/{address_id}")
    assert get_res.status_code == 200
    assert get_res.json()["street"] == "Original Street"

    # 3. Update
    update_payload = {
        "street": "Updated Street",
        "latitude": 12.345
    }
    put_res = client.put(f"/api/v1/addresses/{address_id}", json=update_payload)
    assert put_res.status_code == 200
    updated_data = put_res.json()
    assert updated_data["street"] == "Updated Street"
    assert updated_data["latitude"] == 12.345
    # Non-updated fields should remain the same
    assert updated_data["city"] == "Original City"

    # 4. List and check updated item is present
    list_res = client.get("/api/v1/addresses/")
    assert list_res.status_code == 200
    addresses = list_res.json()
    assert len(addresses) == 1
    assert addresses[0]["id"] == address_id

    # 5. Delete
    del_res = client.delete(f"/api/v1/addresses/{address_id}")
    assert del_res.status_code == 204

    # 6. Read after delete
    get_after_del = client.get(f"/api/v1/addresses/{address_id}")
    assert get_after_del.status_code == 404

def test_distance_search_addresses(client):
    """Test filtering and ordering addresses based on radius search."""
    # Reference center: Googleplex in Mountain View, CA (37.42202, -122.08408)
    googleplex_lat = 37.42202
    googleplex_lon = -122.08408

    # We will seed 4 landmarks:
    # 1. Stanford University: ~8km away
    stanford = {
        "street": "450 Jane Stanford Way",
        "city": "Stanford",
        "state": "CA",
        "country": "USA",
        "postal_code": "94305",
        "latitude": 37.4275,
        "longitude": -122.1697
    }
    # 2. Shoreline Amphitheatre: ~2km away
    shoreline = {
        "street": "1 Amphitheatre Pkwy",
        "city": "Mountain View",
        "state": "CA",
        "country": "USA",
        "postal_code": "94043",
        "latitude": 37.4278,
        "longitude": -122.0902
    }
    # 3. Golden Gate Bridge: ~50km away
    gg_bridge = {
        "street": "Golden Gate Bridge",
        "city": "San Francisco",
        "state": "CA",
        "country": "USA",
        "postal_code": "94129",
        "latitude": 37.8199,
        "longitude": -122.4783
    }
    # 4. Central Park, NY: ~4100km away
    central_park = {
        "street": "Central Park",
        "city": "New York",
        "state": "NY",
        "country": "USA",
        "postal_code": "10024",
        "latitude": 40.7851,
        "longitude": -73.9683
    }

    # Add all landmarks
    for landmark in [stanford, shoreline, gg_bridge, central_park]:
        client.post("/api/v1/addresses/", json=landmark)

    # Search with 10 km radius (should return Shoreline and Stanford, ordered by closest)
    search_res_10k = client.get(
        f"/api/v1/addresses/search?latitude={googleplex_lat}&longitude={googleplex_lon}&radius_km=10.0"
    )
    assert search_res_10k.status_code == 200
    results_10k = search_res_10k.json()
    
    assert len(results_10k) == 2
    # Verify distance calculations are included
    assert "distance_km" in results_10k[0]
    assert "distance_km" in results_10k[1]

    # Verify sorting: Shoreline is closer (~2km) than Stanford (~8km)
    assert results_10k[0]["city"] == "Mountain View"  # Shoreline
    assert results_10k[1]["city"] == "Stanford"      # Stanford
    assert results_10k[0]["distance_km"] < results_10k[1]["distance_km"]

    # Search with 60 km radius (should return Shoreline, Stanford, and Golden Gate Bridge)
    search_res_60k = client.get(
        f"/api/v1/addresses/search?latitude={googleplex_lat}&longitude={googleplex_lon}&radius_km=60.0"
    )
    assert search_res_60k.status_code == 200
    results_60k = search_res_60k.json()
    assert len(results_60k) == 3
    assert results_60k[2]["city"] == "San Francisco"  # Golden Gate Bridge

    # Search with 0.5 km radius (should return empty list as Shoreline is ~0.84km away)
    search_res_1k = client.get(
        f"/api/v1/addresses/search?latitude={googleplex_lat}&longitude={googleplex_lon}&radius_km=0.5"
    )
    assert search_res_1k.status_code == 200
    assert len(search_res_1k.json()) == 0

def test_distance_search_validation(client):
    """Test search endpoint query parameters validation."""
    # Test invalid latitude (>90)
    response = client.get("/api/v1/addresses/search?latitude=90.5&longitude=0.0&radius_km=5.0")
    assert response.status_code == 422

    # Test invalid longitude (<-180)
    response = client.get("/api/v1/addresses/search?latitude=0.0&longitude=-180.5&radius_km=5.0")
    assert response.status_code == 422

    # Test invalid radius (<=0)
    response = client.get("/api/v1/addresses/search?latitude=0.0&longitude=0.0&radius_km=0.0")
    assert response.status_code == 422
