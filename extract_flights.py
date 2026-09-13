import os
import json
import hashlib
import logging
import statistics
import time
from datetime import datetime, timezone, date, timedelta
from typing import Optional, Any, List, Dict, Tuple

import boto3
import requests
from botocore.exceptions import ClientError
from dotenv import load_dotenv


# ============================================================
# INDIA AIRFARE PRICE INDEX (APIx)
# ============================================================
#
# Pipeline:
#
# SerpApi Google Flights
#        ↓
# Dynamic route/date collection
#        ↓
# Standardization
#        ↓
# Deterministic record fingerprint
#        ↓
# In-memory deduplication
#        ↓
# S3 duplicate check
#        ↓
# Store only NEW observations
#        ↓
# APIx calculation
#        ↓
# S3 analytics
#
# IMPORTANT:
#
# Same flight + same fare + same journey details
#     => DUPLICATE → DO NOT STORE AGAIN
#
# Same flight + changed fare
#     => NEW observation → STORE
#
# collection_timestamp is intentionally NOT part
# of the duplicate fingerprint.
#
# ============================================================


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")

# Root folder in S3
S3_ROOT = os.getenv(
    "S3_ROOT",
    "india-airfare-index"
).strip("/")

# Currency
DEFAULT_CURRENCY = os.getenv(
    "CURRENCY",
    "INR"
)

# Search settings
DEFAULT_ADULTS = int(
    os.getenv("ADULTS", "1")
)

DEFAULT_TRAVEL_CLASS = int(
    os.getenv("TRAVEL_CLASS", "1")
)

DEFAULT_STOPS = int(
    os.getenv("STOPS", "0")
)

# Index settings
BASE_INDEX = float(
    os.getenv("BASE_INDEX", "100")
)

BASE_FARE_ENV = os.getenv(
    "BASE_FARE"
)

# API settings
REQUEST_TIMEOUT = int(
    os.getenv("REQUEST_TIMEOUT", "60")
)

MAX_RETRIES = int(
    os.getenv("MAX_RETRIES", "3")
)

RETRY_DELAY = float(
    os.getenv("RETRY_DELAY", "2")
)

# Dynamic route configuration
#
# Example:
#
# ROUTES=DEL-BOM,BLR-DEL,BLR-BOM,DEL-HYD,BOM-HYD
#
ROUTES_ENV = os.getenv(
    "ROUTES",
    "DEL-BOM,BLR-DEL,BLR-BOM,DEL-HYD,BOM-HYD"
)

# Number of future travel days to collect
TRAVEL_DAYS = int(
    os.getenv("TRAVEL_DAYS", "7")
)

# Start date:
#
# AUTO       -> today
# YYYY-MM-DD -> fixed starting date
#
OUTBOUND_START_DATE = os.getenv(
    "OUTBOUND_START_DATE",
    "AUTO"
)

# Optional return trip
#
# RETURN_DAYS=3
#
# Creates return_date = outbound_date + 3 days
#
RETURN_DAYS_ENV = os.getenv(
    "RETURN_DAYS"
)

# Source identifier
SOURCE_NAME = os.getenv(
    "SOURCE_NAME",
    "SerpApi"
)

SOURCE_ENGINE = os.getenv(
    "SOURCE_ENGINE",
    "Google Flights"
)


# ============================================================
# VALIDATION
# ============================================================

if not SERPAPI_API_KEY:
    raise ValueError(
        "SERPAPI_API_KEY is missing"
    )

if not S3_BUCKET:
    raise ValueError(
        "S3_BUCKET_NAME is missing"
    )


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s - "
        "%(levelname)s - "
        "%(message)s"
    )
)

logger = logging.getLogger(__name__)


# ============================================================
# AWS S3 CLIENT
# ============================================================

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def utc_now() -> datetime:
    """
    Return current UTC timestamp.
    """

    return datetime.now(timezone.utc)


def canonical_json(data: Any) -> str:
    """
    Create deterministic JSON representation.

    This makes hashing stable even if dictionary
    ordering changes.
    """

    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str
    )


def sha256_text(value: str) -> str:
    """
    SHA-256 helper.
    """

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def normalize_text(value: Any) -> str:
    """
    Normalize strings:
    - None -> ""
    - remove leading/trailing spaces
    - collapse multiple spaces
    """

    if value is None:
        return ""

    return " ".join(
        str(value).strip().split()
    )


def parse_date(value: str) -> date:
    """
    Parse YYYY-MM-DD.
    """

    return datetime.strptime(
        value,
        "%Y-%m-%d"
    ).date()


def safe_float(value: Any) -> Optional[float]:
    """
    Convert value to float safely.
    """

    try:

        if value is None:
            return None

        return float(value)

    except (
        TypeError,
        ValueError
    ):

        return None


def safe_int(value: Any) -> Optional[int]:
    """
    Convert value to integer safely.
    """

    try:

        if value is None:
            return None

        return int(value)

    except (
        TypeError,
        ValueError
    ):

        return None


# ============================================================
# ROUTE CONFIGURATION
# ============================================================

def get_routes() -> List[Tuple[str, str]]:
    """
    Read routes from environment.

    Example:

        ROUTES=DEL-BOM,BLR-DEL,BLR-HYD

    """

    routes = []

    raw_routes = ROUTES_ENV.split(",")

    for item in raw_routes:

        item = item.strip().upper()

        if not item:
            continue

        if "-" not in item:
            logger.warning(
                "Invalid route ignored: %s",
                item
            )
            continue

        parts = item.split("-")

        if len(parts) != 2:
            logger.warning(
                "Invalid route ignored: %s",
                item
            )
            continue

        departure = parts[0].strip()
        arrival = parts[1].strip()

        if not departure or not arrival:
            continue

        if departure == arrival:

            logger.warning(
                "Same airport route ignored: %s",
                item
            )

            continue

        routes.append(
            (
                departure,
                arrival
            )
        )

    if not routes:

        raise ValueError(
            "No valid routes configured. "
            "Use ROUTES=DEL-BOM,BLR-DEL"
        )

    return routes


# ============================================================
# DYNAMIC DATE GENERATOR
# ============================================================

def get_outbound_dates() -> List[str]:
    """
    Generate dynamic travel dates.

    Example:

        OUTBOUND_START_DATE=AUTO
        TRAVEL_DAYS=7

    produces:

        today
        today + 1
        ...
        today + 6
    """

    if (
        not OUTBOUND_START_DATE
        or OUTBOUND_START_DATE.upper() == "AUTO"
    ):

        start_date = utc_now().date()

    else:

        start_date = parse_date(
            OUTBOUND_START_DATE
        )

    dates = []

    for offset in range(TRAVEL_DAYS):

        current = (
            start_date
            + timedelta(days=offset)
        )

        dates.append(
            current.isoformat()
        )

    return dates


# ============================================================
# RETURN DATE
# ============================================================

def calculate_return_date(
    outbound_date: str
) -> Optional[str]:

    if RETURN_DAYS_ENV is None:
        return None

    return_days = int(
        RETURN_DAYS_ENV
    )

    outbound = parse_date(
        outbound_date
    )

    return_date = (
        outbound
        + timedelta(days=return_days)
    )

    return return_date.isoformat()


# ============================================================
# ADVANCE PURCHASE DAYS
# ============================================================

def calculate_advance_purchase_days(
    collection_timestamp: str,
    outbound_date: str
) -> Optional[int]:
    """
    Booking lead time:

        travel date - collection date

    This directly supports the problem statement's
    requirement to study booking-time effects.
    """

    try:

        collection_date = (
            datetime.fromisoformat(
                collection_timestamp
            ).date()
        )

        travel_date = parse_date(
            outbound_date
        )

        value = (
            travel_date
            - collection_date
        ).days

        return max(value, 0)

    except Exception:

        return None


# ============================================================
# SERPAPI REQUEST
# ============================================================

def fetch_flight_data(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    return_date: Optional[str] = None,
    currency: str = DEFAULT_CURRENCY,
    adults: int = DEFAULT_ADULTS,
    travel_class: int = DEFAULT_TRAVEL_CLASS,
    stops: int = DEFAULT_STOPS
) -> Dict[str, Any]:
    """
    Fetch Google Flights data from SerpApi.

    Includes retry logic for transient failures.
    """

    url = (
        "https://serpapi.com/search"
    )

    params = {

        "engine": "google_flights",

        "api_key": SERPAPI_API_KEY,

        "departure_id": departure_id,

        "arrival_id": arrival_id,

        "outbound_date": outbound_date,

        "currency": currency,

        "adults": adults,

        "travel_class": travel_class,

        "stops": stops,

        "type": (
            1
            if return_date
            else 2
        ),

        "output": "json"
    }

    if return_date:

        params[
            "return_date"
        ] = return_date

    logger.info(
        "Fetching: %s -> %s | outbound=%s | return=%s",
        departure_id,
        arrival_id,
        outbound_date,
        return_date
    )

    last_error = None

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            data = response.json()

            if "error" in data:

                raise RuntimeError(
                    data["error"]
                )

            logger.info(
                "Flight data received successfully"
            )

            return data

        except (
            requests.RequestException,
            ValueError,
            RuntimeError
        ) as exc:

            last_error = exc

            logger.warning(
                "Attempt %d/%d failed: %s",
                attempt,
                MAX_RETRIES,
                exc
            )

            if (
                attempt
                < MAX_RETRIES
            ):

                time.sleep(
                    RETRY_DELAY
                    * attempt
                )

    raise RuntimeError(
        "SerpApi request failed after "
        f"{MAX_RETRIES} attempts: "
        f"{last_error}"
    )


# ============================================================
# S3 OBJECT EXISTS
# ============================================================

def s3_object_exists(
    s3_key: str
) -> bool:
    """
    Check whether an object already exists.
    """

    try:

        s3_client.head_object(
            Bucket=S3_BUCKET,
            Key=s3_key
        )

        return True

    except ClientError as exc:

        error_code = (
            exc.response
            .get("Error", {})
            .get("Code")
        )

        if error_code in (
            "404",
            "NoSuchKey",
            "NotFound"
        ):

            return False

        raise


# ============================================================
# S3 UPLOAD ONLY WHEN NEW
# ============================================================

def upload_json_if_new(
    data: Any,
    s3_key: str,
    metadata: Optional[
        Dict[str, str]
    ] = None
) -> bool:
    """
    Upload only when the deterministic S3 key
    does not already exist.

    Returns:
        True  -> new object uploaded
        False -> duplicate skipped
    """

    if s3_object_exists(
        s3_key
    ):

        logger.info(
            "DUPLICATE SKIPPED: s3://%s/%s",
            S3_BUCKET,
            s3_key
        )

        return False

    json_data = json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
        default=str
    )

    try:

        s3_client.put_object(

            Bucket=S3_BUCKET,

            Key=s3_key,

            Body=json_data.encode(
                "utf-8"
            ),

            ContentType=(
                "application/json"
            ),

            Metadata=metadata or {}
        )

        logger.info(
            "NEW DATA STORED: s3://%s/%s",
            S3_BUCKET,
            s3_key
        )

        return True

    except ClientError as exc:

        logger.error(
            "S3 upload failed: %s",
            exc
        )

        raise


# ============================================================
# FLIGHT EXTRACTION
# ============================================================

def extract_flights(
    raw_data: Dict[str, Any],
    departure_airport: str,
    arrival_airport: str,
    outbound_date: str,
    return_date: Optional[str],
    currency: str
) -> List[Dict[str, Any]]:
    """
    Convert SerpApi response into a standardized
    airfare observation dataset.
    """

    flights = []

    groups = []

    groups.extend(
        raw_data.get(
            "best_flights",
            []
        ) or []
    )

    groups.extend(
        raw_data.get(
            "other_flights",
            []
        ) or []
    )

    collection_timestamp = (
        utc_now().isoformat()
    )

    advance_purchase_days = (
        calculate_advance_purchase_days(
            collection_timestamp,
            outbound_date
        )
    )

    for group in groups:

        segments = (
            group.get(
                "flights",
                []
            )
            or []
        )

        if not segments:
            continue

        first_segment = (
            segments[0]
        )

        last_segment = (
            segments[-1]
        )

        departure = (
            first_segment.get(
                "departure_airport",
                {}
            )
            or {}
        )

        arrival = (
            last_segment.get(
                "arrival_airport",
                {}
            )
            or {}
        )

        price = safe_float(
            group.get("price")
        )

        if (
            price is None
            or price <= 0
        ):
            continue

        departure_code = (
            normalize_text(
                departure.get("id")
                or departure_airport
            )
            .upper()
        )

        arrival_code = (
            normalize_text(
                arrival.get("id")
                or arrival_airport
            )
            .upper()
        )

        airline = normalize_text(
            first_segment.get(
                "airline"
            )
        )

        flight_numbers = []

        for segment in segments:

            flight_number = (
                normalize_text(
                    segment.get(
                        "flight_number"
                    )
                )
            )

            if flight_number:

                flight_numbers.append(
                    flight_number.upper()
                )

        # ----------------------------------------------------
        # Availability information
        #
        # SerpApi response formats can vary.
        # We therefore preserve extensions as raw metadata
        # rather than inventing a seat count.
        # ----------------------------------------------------

        extensions = (
            group.get(
                "extensions"
            )
            or []
        )

        if isinstance(
            extensions,
            list
        ):

            extensions_normalized = [
                normalize_text(x)
                for x in extensions
                if normalize_text(x)
            ]

        else:

            extensions_normalized = [
                normalize_text(
                    extensions
                )
            ]

        sold_out = False

        for extension in (
            extensions_normalized
        ):

            if (
                "sold out"
                in extension.lower()
                or
                "no seats"
                in extension.lower()
            ):

                sold_out = True

        duration_minutes = safe_int(
            group.get(
                "total_duration"
            )
        )

        stops = max(
            len(segments) - 1,
            0
        )

        travel_class = normalize_text(
            first_segment.get(
                "travel_class"
            )
        )

        # ----------------------------------------------------
        # Standardized observation
        # ----------------------------------------------------

        record = {

            # Unique observation timestamp
            "collection_timestamp":
                collection_timestamp,

            # Source
            "source":
                SOURCE_NAME,

            "source_engine":
                SOURCE_ENGINE,

            # Route
            "departure_airport":
                departure_code,

            "arrival_airport":
                arrival_code,

            "route":
                f"{departure_code}-{arrival_code}",

            # Travel dates
            "outbound_date":
                outbound_date,

            "return_date":
                return_date,

            # Booking-time feature
            "advance_purchase_days":
                advance_purchase_days,

            # Carrier
            "airline":
                airline,

            "flight_numbers":
                flight_numbers,

            # Schedule
            "departure_time":
                normalize_text(
                    departure.get(
                        "time"
                    )
                ),

            "arrival_time":
                normalize_text(
                    arrival.get(
                        "time"
                    )
                ),

            "duration_minutes":
                duration_minutes,

            "stops":
                stops,

            # Fare
            "travel_class":
                travel_class,

            "base_fare":
                None,

            "taxes_fees":
                None,

            "total_fare":
                round(
                    price,
                    2
                ),

            "price":
                round(
                    price,
                    2
                ),

            "currency":
                normalize_text(
                    currency
                ).upper(),

            # Availability
            "seats_available":
                None,

            "sold_out":
                sold_out,

            "availability_details":
                extensions_normalized
        }

        # Add deterministic record ID later
        flights.append(
            record
        )

    return flights


# ============================================================
# FLIGHT IDENTITY
# ============================================================

def flight_identity(
    record: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Fields defining uniqueness of a fare observation.

    IMPORTANT:

    collection_timestamp is excluded.

    price IS included.

    Therefore:

        Same flight + same price
            = duplicate

        Same flight + different price
            = new observation
    """

    return {

        "departure_airport":
            record.get(
                "departure_airport"
            ),

        "arrival_airport":
            record.get(
                "arrival_airport"
            ),

        "outbound_date":
            record.get(
                "outbound_date"
            ),

        "return_date":
            record.get(
                "return_date"
            ),

        "airline":
            record.get(
                "airline"
            ),

        "flight_numbers":
            record.get(
                "flight_numbers",
                []
            ),

        "departure_time":
            record.get(
                "departure_time"
            ),

        "arrival_time":
            record.get(
                "arrival_time"
            ),

        "duration_minutes":
            record.get(
                "duration_minutes"
            ),

        "stops":
            record.get(
                "stops"
            ),

        "travel_class":
            record.get(
                "travel_class"
            ),

        "total_fare":
            record.get(
                "total_fare"
            ),

        "currency":
            record.get(
                "currency"
            ),

        "source":
            record.get(
                "source"
            ),

        "source_engine":
            record.get(
                "source_engine"
            )
    }


# ============================================================
# DETERMINISTIC RECORD ID
# ============================================================

def generate_record_id(
    record: Dict[str, Any]
) -> str:
    """
    Generate SHA-256 fingerprint.

    This ID is used as the S3 object identity.
    """

    identity = flight_identity(
        record
    )

    return sha256_text(
        canonical_json(
            identity
        )
    )


def add_record_id(
    record: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add deterministic record_id.
    """

    result = dict(record)

    result[
        "record_id"
    ] = generate_record_id(
        result
    )

    return result


# ============================================================
# IN-MEMORY DEDUPLICATION
# ============================================================

def deduplicate_flights(
    flights: List[Dict[str, Any]]
) -> Tuple[
    List[Dict[str, Any]],
    int
]:
    """
    Remove duplicate observations
    from the current SerpApi response.
    """

    unique = {}

    duplicate_count = 0

    for flight in flights:

        flight = add_record_id(
            flight
        )

        record_id = (
            flight["record_id"]
        )

        if record_id in unique:

            duplicate_count += 1

            continue

        unique[
            record_id
        ] = flight

    return (
        list(unique.values()),
        duplicate_count
    )


# ============================================================
# S3 KEY GENERATORS
# ============================================================

def build_raw_s3_key(
    collection_date: datetime,
    departure_airport: str,
    arrival_airport: str,
    outbound_date: str,
    raw_hash: str
) -> str:
    """
    Raw API response is stored using content hash.

    Exact same response:
        same hash
        same S3 key
        duplicate skipped
    """

    return (

        f"{S3_ROOT}/raw/flights/"

        f"year={collection_date.year}/"

        f"month={collection_date.month:02d}/"

        f"day={collection_date.day:02d}/"

        f"route={departure_airport}-"
        f"{arrival_airport}/"

        f"outbound_date="
        f"{outbound_date}/"

        f"response_hash="
        f"{raw_hash}.json"
    )


def build_processed_s3_key(
    record: Dict[str, Any]
) -> str:
    """
    Processed data uses record_id as the final
    S3 identity.

    This prevents duplicate observations.
    """

    collection_date = (
        record[
            "collection_timestamp"
        ][:10]
        .replace(
            "-",
            "/"
        )
    )

    route = (
        record[
            "departure_airport"
        ]
        + "-"
        + record[
            "arrival_airport"
        ]
    )

    return (

        f"{S3_ROOT}/processed/flights/"

        f"collection_date="
        f"{collection_date}/"

        f"route={route}/"

        f"outbound_date="
        f"{record['outbound_date']}/"

        f"record_id="
        f"{record['record_id']}.json"
    )


def build_api_x_s3_key(
    record: Dict[str, Any],
    analytics_hash: str
) -> str:
    """
    APIx snapshots are also hash-based.

    Therefore:
        same calculation = duplicate
        changed calculation = new snapshot
    """

    collection_date = (
        record[
            "collection_timestamp"
        ][:10]
        .replace(
            "-",
            "/"
        )
    )

    route = (
        record[
            "departure_airport"
        ]
        + "-"
        + record[
            "arrival_airport"
        ]
    )

    return (

        f"{S3_ROOT}/analytics/"
        f"airfare_index/"

        f"collection_date="
        f"{collection_date}/"

        f"route={route}/"

        f"outbound_date="
        f"{record['outbound_date']}/"

        f"APIx_"
        f"{analytics_hash}.json"
    )


# ============================================================
# SAVE UNIQUE FLIGHTS
# ============================================================

def save_unique_flights(
    flights: List[Dict[str, Any]]
) -> Dict[str, int]:
    """
    Save each unique flight observation.

    Existing record_id:
        skip

    New record_id:
        upload
    """

    uploaded = 0

    skipped = 0

    for flight in flights:

        s3_key = (
            build_processed_s3_key(
                flight
            )
        )

        is_new = (
            upload_json_if_new(
                flight,
                s3_key,
                metadata={

                    "record_id":
                        flight[
                            "record_id"
                        ],

                    "route":
                        flight[
                            "route"
                        ],

                    "source":
                        SOURCE_NAME
                }
            )
        )

        if is_new:

            uploaded += 1

        else:

            skipped += 1

    return {

        "uploaded":
            uploaded,

        "skipped_duplicates":
            skipped
    }


# ============================================================
# RAW DATA HASH
# ============================================================

def generate_raw_hash(
    raw_data: Dict[str, Any]
) -> str:
    """
    Generate hash for complete SerpApi response.
    """

    return sha256_text(
        canonical_json(
            raw_data
        )
    )


# ============================================================
# APIx CALCULATION
# ============================================================

def calculate_api_x(
    flights: List[Dict[str, Any]],
    base_index: float = BASE_INDEX
) -> Optional[Dict[str, Any]]:
    """
    Prototype Airfare Price Index.

    APIx =
        (Current Average Fare / Base Fare)
        * Base Index

    Later, for the final SIH solution, this can be replaced
    by fixed route/carrier weights aligned to CPI methodology.
    """

    if not flights:
        return None

    prices = [

        float(
            flight["total_fare"]
        )

        for flight in flights

        if flight.get(
            "total_fare"
        ) is not None
    ]

    if not prices:
        return None

    average_price = (
        statistics.mean(
            prices
        )
    )

    median_price = (
        statistics.median(
            prices
        )
    )

    minimum_price = min(
        prices
    )

    maximum_price = max(
        prices
    )

    if BASE_FARE_ENV:

        base_fare = float(
            BASE_FARE_ENV
        )

    else:

        base_fare = (
            average_price
        )

    if base_fare <= 0:
        return None

    api_x = (

        average_price
        /
        base_fare
        *
        base_index
    )

    route = (
        flights[0][
            "departure_airport"
        ]
        + "-"
        + flights[0][
            "arrival_airport"
        ]
    )

    result = {

        "index_name":
            "Airfare Price Index",

        "index_code":
            "APIx",

        "index_value":
            round(
                api_x,
                2
            ),

        "base_index":
            base_index,

        "base_fare":
            round(
                base_fare,
                2
            ),

        "average_fare":
            round(
                average_price,
                2
            ),

        "median_fare":
            round(
                median_price,
                2
            ),

        "minimum_fare":
            round(
                minimum_price,
                2
            ),

        "maximum_fare":
            round(
                maximum_price,
                2
            ),

        "sample_size":
            len(prices),

        "currency":
            flights[0].get(
                "currency",
                DEFAULT_CURRENCY
            ),

        "route":
            route,

        "outbound_date":
            flights[0].get(
                "outbound_date"
            ),

        "advance_purchase_days":
            flights[0].get(
                "advance_purchase_days"
            ),

        "calculated_at":
            utc_now().isoformat()
    }

    return result


# ============================================================
# APIx HASH
# ============================================================

def calculate_api_x_hash(
    api_x: Dict[str, Any]
) -> str:
    """
    Hash only deterministic APIx content.

    calculated_at is excluded so that repeated
    execution does not generate duplicate index files.
    """

    identity = dict(
        api_x
    )

    identity.pop(
        "calculated_at",
        None
    )

    return sha256_text(
        canonical_json(
            identity
        )
    )


# ============================================================
# RUN MANIFEST
# ============================================================

def create_run_manifest(
    *,
    run_id: str,
    route: str,
    outbound_date: str,
    extracted: int,
    duplicates_in_response: int,
    uploaded: int,
    skipped_s3: int,
    raw_uploaded: bool,
    api_x: Optional[
        Dict[str, Any]
    ]
) -> Dict[str, Any]:
    """
    Create a compact execution manifest.

    Useful for monitoring the pipeline.
    """

    return {

        "run_id":
            run_id,

        "pipeline":
            "india-airfare-index",

        "route":
            route,

        "outbound_date":
            outbound_date,

        "run_timestamp":
            utc_now().isoformat(),

        "records_extracted":
            extracted,

        "duplicates_in_api_response":
            duplicates_in_response,

        "new_records_uploaded":
            uploaded,

        "existing_records_skipped":
            skipped_s3,

        "raw_response_uploaded":
            raw_uploaded,

        "api_x_generated":
            api_x is not None,

        "api_x_value":
            (
                api_x["index_value"]
                if api_x
                else None
            )
    }


# ============================================================
# SAVE RUN MANIFEST
# ============================================================

def save_run_manifest(
    manifest: Dict[str, Any]
) -> None:
    """
    Store one run manifest.

    run_id makes every execution traceable.
    """

    run_date = (
        manifest[
            "run_timestamp"
        ][:10]
        .replace(
            "-",
            "/"
        )
    )

    run_id = manifest[
        "run_id"
    ]

    s3_key = (

        f"{S3_ROOT}/runs/"

        f"date={run_date}/"

        f"run_id={run_id}.json"
    )

    upload_json_if_new(
        manifest,
        s3_key
    )


# ============================================================
# PROCESS ONE SEARCH
# ============================================================

def process_search(
    departure_airport: str,
    arrival_airport: str,
    outbound_date: str
) -> Dict[str, Any]:
    """
    Process one route + one travel date.
    """

    run_id = hashlib.sha256(

        (
            f"{departure_airport}|"
            f"{arrival_airport}|"
            f"{outbound_date}|"
            f"{utc_now().isoformat()}"
        ).encode(
            "utf-8"
        )

    ).hexdigest()[:16]

    collection_date = utc_now()

    return_date = (
        calculate_return_date(
            outbound_date
        )
    )

    route = (

        f"{departure_airport}-"
        f"{arrival_airport}"
    )

    logger.info(
        ""
    )

    logger.info(
        "=" * 80
    )

    logger.info(
        "PROCESSING ROUTE: %s",
        route
    )

    logger.info(
        "TRAVEL DATE: %s",
        outbound_date
    )

    logger.info(
        "RUN ID: %s",
        run_id
    )

    logger.info(
        "=" * 80
    )

    # --------------------------------------------------------
    # 1. FETCH
    # --------------------------------------------------------

    raw_data = fetch_flight_data(

        departure_id=
            departure_airport,

        arrival_id=
            arrival_airport,

        outbound_date=
            outbound_date,

        return_date=
            return_date
    )

    # --------------------------------------------------------
    # 2. RAW RESPONSE HASH
    # --------------------------------------------------------

    raw_hash = generate_raw_hash(
        raw_data
    )

    raw_key = build_raw_s3_key(

        collection_date=
            collection_date,

        departure_airport=
            departure_airport,

        arrival_airport=
            arrival_airport,

        outbound_date=
            outbound_date,

        raw_hash=
            raw_hash
    )

    raw_uploaded = (
        upload_json_if_new(

            raw_data,

            raw_key,

            metadata={

                "response_hash":
                    raw_hash,

                "route":
                    route,

                "outbound_date":
                    outbound_date,

                "source":
                    SOURCE_NAME
            }
        )
    )

    # --------------------------------------------------------
    # 3. TRANSFORM
    # --------------------------------------------------------

    flights = extract_flights(

        raw_data=
            raw_data,

        departure_airport=
            departure_airport,

        arrival_airport=
            arrival_airport,

        outbound_date=
            outbound_date,

        return_date=
            return_date,

        currency=
            DEFAULT_CURRENCY
    )

    extracted_count = len(
        flights
    )

    logger.info(
        "Extracted records: %d",
        extracted_count
    )

    # --------------------------------------------------------
    # 4. CURRENT-RESPONSE DEDUPLICATION
    # --------------------------------------------------------

    flights, duplicate_count = (
        deduplicate_flights(
            flights
        )
    )

    logger.info(
        "Duplicates in API response removed: %d",
        duplicate_count
    )

    logger.info(
        "Unique records from response: %d",
        len(flights)
    )

    # --------------------------------------------------------
    # 5. SAVE ONLY NEW RECORDS TO S3
    # --------------------------------------------------------

    save_result = (
        save_unique_flights(
            flights
        )
    )

    uploaded = save_result[
        "uploaded"
    ]

    skipped_s3 = save_result[
        "skipped_duplicates"
    ]

    logger.info(
        "NEW S3 records: %d",
        uploaded
    )

    logger.info(
        "EXISTING S3 records skipped: %d",
        skipped_s3
    )

    # --------------------------------------------------------
    # 6. APIx
    # --------------------------------------------------------

    api_x = calculate_api_x(
        flights=flights,
        base_index=BASE_INDEX
    )

    api_x_s3_key = None

    if api_x:

        api_x_hash = (
            calculate_api_x_hash(
                api_x
            )
        )

        # Use one processed record as the route/date
        # reference for the key.
        reference_record = flights[0]

        api_x_s3_key = (
            build_api_x_s3_key(

                reference_record,

                api_x_hash
            )
        )

        upload_json_if_new(

            api_x,

            api_x_s3_key,

            metadata={

                "index_code":
                    "APIx",

                "route":
                    route,

                "outbound_date":
                    outbound_date
            }
        )

        logger.info(
            "APIx value: %.2f",
            api_x[
                "index_value"
            ]
        )

    else:

        logger.warning(
            "APIx could not be calculated"
        )

    # --------------------------------------------------------
    # 7. RUN MANIFEST
    # --------------------------------------------------------

    manifest = (
        create_run_manifest(

            run_id=
                run_id,

            route=
                route,

            outbound_date=
                outbound_date,

            extracted=
                extracted_count,

            duplicates_in_response=
                duplicate_count,

            uploaded=
                uploaded,

            skipped_s3=
                skipped_s3,

            raw_uploaded=
                raw_uploaded,

            api_x=
                api_x
        )
    )

    save_run_manifest(
        manifest
    )

    return {

        "route":
            route,

        "outbound_date":
            outbound_date,

        "run_id":
            run_id,

        "extracted":
            extracted_count,

        "duplicates_in_api":
            duplicate_count,

        "new_records":
            uploaded,

        "skipped_existing":
            skipped_s3,

        "raw_uploaded":
            raw_uploaded,

        "api_x":
            (
                api_x[
                    "index_value"
                ]
                if api_x
                else None
            )
    }


# ============================================================
# MAIN
# ============================================================

def main():

    logger.info(
        ""
    )

    logger.info(
        "#" * 80
    )

    logger.info(
        "INDIA AIRFARE INDEX PIPELINE"
    )

    logger.info(
        "#" * 80
    )

    logger.info(
        "S3 Bucket: %s",
        S3_BUCKET
    )

    logger.info(
        "AWS Region: %s",
        AWS_REGION
    )

    logger.info(
        "Routes: %s",
        ROUTES_ENV
    )

    logger.info(
        "Travel days: %d",
        TRAVEL_DAYS
    )

    # --------------------------------------------------------
    # Dynamic routes
    # --------------------------------------------------------

    routes = get_routes()

    # --------------------------------------------------------
    # Dynamic outbound dates
    # --------------------------------------------------------

    outbound_dates = (
        get_outbound_dates()
    )

    logger.info(
        "Routes to process: %d",
        len(routes)
    )

    logger.info(
        "Travel dates to process: %d",
        len(outbound_dates)
    )

    total_searches = 0
    total_extracted = 0
    total_new = 0
    total_skipped = 0
    total_duplicates = 0
    total_raw_new = 0

    results = []

    # ========================================================
    # ROUTE × DATE MATRIX
    # ========================================================

    for departure_airport, arrival_airport in routes:

        for outbound_date in outbound_dates:

            total_searches += 1

            try:

                result = process_search(

                    departure_airport=
                        departure_airport,

                    arrival_airport=
                        arrival_airport,

                    outbound_date=
                        outbound_date
                )

                results.append(
                    result
                )

                total_extracted += (
                    result[
                        "extracted"
                    ]
                )

                total_duplicates += (
                    result[
                        "duplicates_in_api"
                    ]
                )

                total_new += (
                    result[
                        "new_records"
                    ]
                )

                total_skipped += (
                    result[
                        "skipped_existing"
                    ]
                )

                if result[
                    "raw_uploaded"
                ]:

                    total_raw_new += 1

            except Exception as exc:

                logger.exception(

                    "Search failed for "
                    "%s -> %s | %s | %s",

                    departure_airport,

                    arrival_airport,

                    outbound_date,

                    exc
                )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    logger.info(
        ""
    )

    logger.info(
        "#" * 80
    )

    logger.info(
        "PIPELINE COMPLETED"
    )

    logger.info(
        "#" * 80
    )

    logger.info(
        "Total searches: %d",
        total_searches
    )

    logger.info(
        "Total extracted: %d",
        total_extracted
    )

    logger.info(
        "Duplicates removed inside API: %d",
        total_duplicates
    )

    logger.info(
        "NEW records uploaded to S3: %d",
        total_new
    )

    logger.info(
        "Existing records skipped: %d",
        total_skipped
    )

    logger.info(
        "NEW raw responses uploaded: %d",
        total_raw_new
    )

    logger.info(
        "S3 bucket: s3://%s/%s",
        S3_BUCKET,
        S3_ROOT
    )

    logger.info(
        "#" * 80
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        logger.warning(
            "Pipeline stopped by user."
        )

    except Exception as exc:

        logger.exception(
            "Pipeline failed: %s",
            exc
        )

        raise