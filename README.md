# Address Book API

A minimal, robust, and optimized REST API built with Python 3, FastAPI, and SQLAlchemy (v2.0) that acts as an Address Book with coordinates validation and distance-based searching. It stores data in a local SQLite database.

---

## Technical Highlights & Optimizations

* **FastAPI Lifespan Context**: Programmatically initializes standard Python logging and automatically creates SQLite database tables on startup.
* **Declarative Schema Validation**: Enforces coordinate limits (Latitude: `-90.0` to `90.0`, Longitude: `-180.0` to `180.0`) and non-empty trimmed strings at the API layer using Pydantic v2.
* **Geospatial Query Optimization**: 
  Instead of fetching all addresses and running math filters on every row, the search algorithm implements a **bounding box (bounding rectangle)** filter in SQL first:
  1. Computes the minimum/maximum latitudes and longitudes for the target radius.
  2. Queries the database using `latitude BETWEEN :min_lat AND :max_lat AND longitude BETWEEN :min_lon AND :max_lon`.
  3. Uses **database indexes** on both coordinate columns for $O(\log N)$ retrieval.
  4. Computes precise distances using the **Haversine formula** in Python only on the filtered candidates, sorting the closest items first.
* **Clean Logging & Robust Exception Handling**: Implements a global middleware handler to capture unexpected errors, preventing server stack trace leaks to client responses.

---

## Project Structure

```text
d:\code interview\
├── app/
│   ├── __init__.py
│   ├── main.py             # Application startup and global exception handlers
│   ├── config.py           # Settings management with pydantic-settings
│   ├── database.py         # SQLAlchemy engine and session dependency
│   ├── models.py           # Indexed database schemas (SQLAlchemy)
│   ├── schemas.py          # Data validation schemas (Pydantic v2)
│   ├── crud.py             # Database operations & optimized search calculations
│   ├── utils.py            # Haversine distance and Bounding Box math functions
│   ├── logging_config.py   # Structured logging configuration
│   └── routers/
│       ├── __init__.py
│       └── addresses.py    # Addresses endpoints (CRUD + Search)
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Testing database overrides and client fixtures
│   └── test_addresses.py   # Coordinate range, CRUD, and distance search tests
├── .env                    # Environment settings configuration
├── .gitignore              # Standard Python gitignore rules
├── requirements.txt        # Third-party dependency definitions
└── README.md               # Setup and execution guide
```

---

## Installation & Setup

Ensure you have **Python 3.10+** installed. Follow these terminal commands to initialize the project:

### 1. Create a Virtual Environment
```bash
python -m venv .venv
```

### 2. Activate the Virtual Environment
* **Windows (Command Prompt / PowerShell)**:
  ```powershell
  .venv\Scripts\activate
  ```
* **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create and Edit `.env`
Create a `.env` file in the root directory (a default one has been pre-created):
```env
PROJECT_NAME="Address Book API"
API_V1_STR="/api/v1"
DATABASE_URL="sqlite:///./addresses.db"
```

---

## Running the Application

Start the development server using Uvicorn:

```bash
python -m uvicorn app.main:app --reload
```

* The SQLite database file (`addresses.db`) will be automatically created in the root folder upon startup.
* The server will run at `http://127.0.0.1:8000`.

### Interactive API Documentation
Navigate to **`http://127.0.0.1:8000/docs`** in your browser to access the built-in interactive **Swagger UI** to test the API endpoints directly.

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **POST** | `/api/v1/addresses/` | Create a new address with validation constraints |
| **GET** | `/api/v1/addresses/` | List addresses (paginated) |
| **GET** | `/api/v1/addresses/{address_id}` | Retrieve details of a specific address by its ID |
| **PUT** | `/api/v1/addresses/{address_id}` | Update fields of an existing address |
| **DELETE**| `/api/v1/addresses/{address_id}`| Delete an address |
| **GET** | `/api/v1/addresses/search` | Search addresses within a given distance from a coordinate |

### Example Search Query
`GET /api/v1/addresses/search?latitude=37.4220&longitude=-122.0841&radius_km=10`
Returns addresses within 10 km of the target coordinates, sorted by proximity, complete with the calculated `distance_km` value in each item.

---

## Running Tests

Automated integration and unit tests are configured using `pytest` and run against an isolated, in-memory database instance.

To execute the test suite:
```bash
python -m pytest -v
```
