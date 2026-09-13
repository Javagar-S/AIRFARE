import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DATA_DIR = PROJECT_ROOT / "data"

CLEANED_DIR = DATA_DIR / "cleaned"

PROCESSED_DIR = DATA_DIR / "processed"


CLEANED_DIR.mkdir(
    parents=True,
    exist_ok=True
)

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# INPUT FILES
# ============================================================

SEARCH_FILE = (
    DATA_DIR / "flight_searches.csv"
)

OPTIONS_FILE = (
    DATA_DIR / "flight_options.csv"
)

LEGS_FILE = (
    DATA_DIR / "flight_legs.csv"
)


# ============================================================
# OUTPUT FILES
# ============================================================

CLEANED_FILE = (
    CLEANED_DIR / "airfare_cleaned.parquet"
)

PROCESSED_FILE = (
    PROCESSED_DIR / "airfare_preprocessed.parquet"
)

CLEANED_CSV = (
    CLEANED_DIR / "airfare_cleaned.csv"
)

PROCESSED_CSV = (
    PROCESSED_DIR / "airfare_preprocessed.csv"
)


# ============================================================
# SAFE CONVERSION HELPERS
# ============================================================

def safe_numeric(
    series: pd.Series
) -> pd.Series:

    return pd.to_numeric(
        series,
        errors="coerce"
    )


def clean_string(
    series: pd.Series
) -> pd.Series:

    return (
        series
        .astype("string")
        .str.strip()
        .str.replace(
            r"\s+",
            " ",
            regex=True
        )
    )


# ============================================================
# LOAD SEARCHES
# ============================================================

def load_searches() -> pd.DataFrame:

    if not SEARCH_FILE.exists():

        raise FileNotFoundError(
            f"Search file not found: "
            f"{SEARCH_FILE}"
        )

    logger.info(
        "Loading search data: %s",
        SEARCH_FILE
    )

    df = pd.read_csv(
        SEARCH_FILE
    )

    logger.info(
        "Search records loaded: %d",
        len(df)
    )

    required = {
        "id",
        "origin",
        "destination",
        "outbound_date",
        "return_date",
        "currency",
        "searched_at"
    }

    missing = (
        required
        - set(df.columns)
    )

    if missing:

        raise ValueError(
            "Missing search columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    # --------------------------------------------------------
    # Clean text
    # --------------------------------------------------------

    for column in [
        "origin",
        "destination",
        "currency",
        "serpapi_search_id"
    ]:

        if column in df.columns:

            df[column] = clean_string(
                df[column]
            )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    df[
        "outbound_date"
    ] = pd.to_datetime(
        df["outbound_date"],
        errors="coerce"
    )

    df[
        "return_date"
    ] = pd.to_datetime(
        df["return_date"],
        errors="coerce"
    )

    df[
        "searched_at"
    ] = pd.to_datetime(
        df["searched_at"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

    df["id"] = safe_numeric(
        df["id"]
    ).astype("Int64")

    # --------------------------------------------------------
    # Remove invalid searches
    # --------------------------------------------------------

    df = df.dropna(
        subset=[
            "id",
            "origin",
            "destination",
            "outbound_date",
            "searched_at"
        ]
    )

    # --------------------------------------------------------
    # Normalize airport codes
    # --------------------------------------------------------

    df["origin"] = (
        df["origin"]
        .str.upper()
    )

    df["destination"] = (
        df["destination"]
        .str.upper()
    )

    # --------------------------------------------------------
    # Remove impossible routes
    # --------------------------------------------------------

    df = df[
        df["origin"]
        !=
        df["destination"]
    ]

    # --------------------------------------------------------
    # Remove duplicate search IDs
    # --------------------------------------------------------

    df = df.drop_duplicates(
        subset=["id"],
        keep="last"
    )

    return df.reset_index(
        drop=True
    )


# ============================================================
# LOAD FLIGHT OPTIONS
# ============================================================

def load_flight_options() -> pd.DataFrame:

    if not OPTIONS_FILE.exists():

        raise FileNotFoundError(
            f"Flight options file not found: "
            f"{OPTIONS_FILE}"
        )

    logger.info(
        "Loading flight options: %s",
        OPTIONS_FILE
    )

    df = pd.read_csv(
        OPTIONS_FILE
    )

    logger.info(
        "Flight option records loaded: %d",
        len(df)
    )

    required = {

        "id",
        "search_id",
        "origin",
        "destination",
        "outbound_date",
        "return_date",
        "price",
        "currency",
        "total_duration_minutes",
        "flight_type",
        "airline",
        "stops",
        "carbon_emissions_kg",
        "booking_token",
        "collected_at"
    }

    missing = (
        required
        - set(df.columns)
    )

    if missing:

        raise ValueError(
            "Missing flight option columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    # --------------------------------------------------------
    # Text columns
    # --------------------------------------------------------

    for column in [
        "origin",
        "destination",
        "currency",
        "flight_type",
        "airline",
        "booking_token"
    ]:

        df[column] = clean_string(
            df[column]
        )

    # --------------------------------------------------------
    # Uppercase airport/currency
    # --------------------------------------------------------

    df["origin"] = (
        df["origin"]
        .str.upper()
    )

    df["destination"] = (
        df["destination"]
        .str.upper()
    )

    df["currency"] = (
        df["currency"]
        .str.upper()
    )

    # --------------------------------------------------------
    # Numeric
    # --------------------------------------------------------

    for column in [
        "id",
        "search_id",
        "price",
        "total_duration_minutes",
        "stops",
        "carbon_emissions_kg"
    ]:

        df[column] = safe_numeric(
            df[column]
        )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    df[
        "outbound_date"
    ] = pd.to_datetime(
        df["outbound_date"],
        errors="coerce"
    )

    df[
        "return_date"
    ] = pd.to_datetime(
        df["return_date"],
        errors="coerce"
    )

    df[
        "collected_at"
    ] = pd.to_datetime(
        df["collected_at"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Remove invalid rows
    # --------------------------------------------------------

    df = df.dropna(
        subset=[
            "id",
            "search_id",
            "origin",
            "destination",
            "outbound_date",
            "price",
            "airline",
            "collected_at"
        ]
    )

    # --------------------------------------------------------
    # Fare validation
    # --------------------------------------------------------

    df = df[
        df["price"] > 0
    ]

    # --------------------------------------------------------
    # Stops validation
    # --------------------------------------------------------

    df.loc[
        df["stops"] < 0,
        "stops"
    ] = np.nan

    df["stops"] = (
        df["stops"]
        .fillna(0)
        .astype(int)
    )

    # --------------------------------------------------------
    # Duration validation
    # --------------------------------------------------------

    df.loc[
        df[
            "total_duration_minutes"
        ] <= 0,
        "total_duration_minutes"
    ] = np.nan

    return df.reset_index(
        drop=True
    )


# ============================================================
# JOIN SEARCH METADATA
# ============================================================

def join_search_metadata(
    searches: pd.DataFrame,
    options: pd.DataFrame
) -> pd.DataFrame:

    search_columns = [

        "id",

        "currency",

        "searched_at",

        "serpapi_search_id"
    ]

    available = [
        column
        for column in search_columns
        if column in searches.columns
    ]

    lookup = searches[
        available
    ].copy()

    lookup = lookup.rename(
        columns={

            "id":
                "search_id",

            "currency":
                "search_currency",

            "searched_at":
                "search_timestamp",

            "serpapi_search_id":
                "search_request_id"
        }
    )

    df = options.merge(
        lookup,
        on="search_id",
        how="left"
    )

    return df

# ============================================================
# SEARCH / OBSERVATION CONSISTENCY
# ============================================================

def standardize_route_fields(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = df.copy()

    # Prefer option-level route
    # because that describes the actual option.

    df["origin"] = (
        df["origin"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["destination"] = (
        df["destination"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["route"] = (
        df["origin"]
        + "-"
        +
        df["destination"]
    )

    return df


# ============================================================
# COLLECTION / BOOKING FEATURES
# ============================================================

def create_booking_features(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = df.copy()

    df[
        "collection_timestamp"
    ] = df[
        "collected_at"
    ]

    # Date only
    df[
        "collection_date"
    ] = (
        df[
            "collection_timestamp"
        ].dt.normalize()
    )

    # Advance purchase days
    df[
        "advance_purchase_days"
    ] = (
        df[
            "outbound_date"
        ]
        -
        df[
            "collection_date"
        ]
    ).dt.days

    # Prevent negative values due to timezone/date
    # inconsistencies.
    df[
        "advance_purchase_days"
    ] = (
        df[
            "advance_purchase_days"
        ]
        .clip(lower=0)
    )

    # Booking-window category
    df[
        "booking_window_category"
    ] = pd.cut(

        df[
            "advance_purchase_days"
        ],

        bins=[
            -1,
            3,
            7,
            14,
            30,
            60,
            np.inf
        ],

        labels=[
            "0-3 days",
            "4-7 days",
            "8-14 days",
            "15-30 days",
            "31-60 days",
            "60+ days"
        ]
    )

    return df


# ============================================================
# TIME FEATURES
# ============================================================

def create_time_features(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = df.copy()

    df[
        "travel_year"
    ] = (
        df[
            "outbound_date"
        ].dt.year
    )

    df[
        "travel_month"
    ] = (
        df[
            "outbound_date"
        ].dt.month
    )

    df[
        "travel_week"
    ] = (
        df[
            "outbound_date"
        ]
        .dt.isocalendar()
        .week
        .astype(int)
    )

    df[
        "travel_day"
    ] = (
        df[
            "outbound_date"
        ].dt.day
    )

    df[
        "travel_day_of_week"
    ] = (
        df[
            "outbound_date"
        ].dt.dayofweek
    )

    df[
        "travel_day_name"
    ] = (
        df[
            "outbound_date"
        ].dt.day_name()
    )

    df[
        "is_weekend"
    ] = (
        df[
            "travel_day_of_week"
        ] >= 5
    )

    df[
        "travel_month_name"
    ] = (
        df[
            "outbound_date"
        ].dt.month_name()
    )

    df[
        "collection_hour"
    ] = (
        df[
            "collection_timestamp"
        ].dt.hour
    )

    return df


# ============================================================
# FARE FEATURES
# ============================================================

def create_fare_features(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = df.copy()

    # Standard total fare
    df[
        "total_fare"
    ] = df[
        "price"
    ].round(2)

    df[
        "fare_band"
    ] = pd.cut(

        df[
            "total_fare"
        ],

        bins=[
            0,
            3000,
            5000,
            7500,
            10000,
            15000,
            25000,
            np.inf
        ],

        labels=[
            "0-3000",
            "3001-5000",
            "5001-7500",
            "7501-10000",
            "10001-15000",
            "15001-25000",
            "25000+"
        ]
    )

    df[
        "log_fare"
    ] = np.log1p(
        df["total_fare"]
    )

    return df

# ============================================================
# DUPLICATE DETECTION
# ============================================================

def remove_duplicate_observations(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Remove true duplicate observations.

    IMPORTANT:
    We preserve historical observations collected at
    different times/dates.

    Same fare on different collection dates:
        KEEP

    Same observation repeated inside the same search:
        REMOVE
    """

    df = df.copy()

    before = len(df)

    # --------------------------------------------------------
    # Collection date is important.
    #
    # The same fare observed on another day is historical data,
    # NOT a duplicate.
    # --------------------------------------------------------

    if "collection_timestamp" in df.columns:

        df["collection_day"] = (
            pd.to_datetime(
                df["collection_timestamp"],
                errors="coerce"
            )
            .dt.date
        )

    else:

        df["collection_day"] = pd.NaT

    duplicate_columns = [

        "search_id",

        "collection_day",

        "origin",

        "destination",

        "outbound_date",

        "return_date",

        "airline",

        "price",

        "currency",

        "total_duration_minutes",

        "flight_type",

        "stops"
    ]

    available = [
        column
        for column in duplicate_columns
        if column in df.columns
    ]

    df = df.drop_duplicates(
        subset=available,
        keep="last"
    )

    removed = before - len(df)

    logger.info(
        "Duplicate observations removed: %d",
        removed
    )

    df = df.drop(
        columns=["collection_day"],
        errors="ignore"
    )

    return df.reset_index(
        drop=True
    )
# ============================================================
# RECORD ID
# ============================================================

def create_record_id(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Generate a deterministic observation ID.

    Historical observations are preserved because the
    collection date is part of the observation identity.
    """

    import hashlib

    df = df.copy()

    # --------------------------------------------------------
    # Collection day
    # --------------------------------------------------------

    df["observation_date"] = (
        pd.to_datetime(
            df["collection_timestamp"],
            errors="coerce"
        )
        .dt.strftime(
            "%Y-%m-%d"
        )
    )

    identity_columns = [

        "search_id",

        "observation_date",

        "origin",

        "destination",

        "outbound_date",

        "return_date",

        "airline",

        "price",

        "currency",

        "total_duration_minutes",

        "flight_type",

        "stops"
    ]

    available = [
        column
        for column in identity_columns
        if column in df.columns
    ]

    identity = (
        df[available]
        .fillna("")
        .astype(str)
        .agg(
            "|".join,
            axis=1
        )
    )

    def generate_hash(
        value: str
    ) -> str:

        return hashlib.sha256(
            value.encode(
                "utf-8"
            )
        ).hexdigest()

    df["record_id"] = (
        identity.map(
            generate_hash
        )
    )

    df = df.drop(
        columns=[
            "observation_date"
        ],
        errors="ignore"
    )

    return df

# ============================================================
# OUTLIER DETECTION
# ============================================================

def create_outlier_features(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = df.copy()

    # Route-level IQR
    def route_outlier(
        group
    ):

        if len(group) < 4:

            group[
                "fare_outlier"
            ] = False

            return group

        q1 = group[
            "total_fare"
        ].quantile(
            0.25
        )

        q3 = group[
            "total_fare"
        ].quantile(
            0.75
        )

        iqr = q3 - q1

        if iqr == 0:

            group[
                "fare_outlier"
            ] = False

            return group

        lower = (
            q1
            - 1.5 * iqr
        )

        upper = (
            q3
            + 1.5 * iqr
        )

        group[
            "fare_outlier"
        ] = (

            (
                group[
                    "total_fare"
                ]
                < lower
            )

            |

            (
                group[
                    "total_fare"
                ]
                > upper
            )
        )

        return group

    df = (
        df.groupby(
            "route",
            group_keys=False
        )
        .apply(
            route_outlier,
            include_groups=False
        )
        .reset_index(
            drop=True
        )
    )

    return df
# ============================================================
# OUTLIER DETECTION
# ============================================================

def create_outlier_features(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Detect airfare outliers using route-level IQR.

    Important:
    - Does NOT delete outliers.
    - Only flags them.
    - Keeps the route column intact.
    """

    df = df.copy()

    # --------------------------------------------------------
    # Safety checks
    # --------------------------------------------------------

    if df.empty:
        df["fare_outlier"] = False
        return df

    if "route" not in df.columns:
        raise KeyError(
            "Column 'route' is missing before outlier detection."
        )

    if "total_fare" not in df.columns:
        df["fare_outlier"] = False
        return df

    # --------------------------------------------------------
    # Ensure fare is numeric
    # --------------------------------------------------------

    df["total_fare"] = pd.to_numeric(
        df["total_fare"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Calculate route-level Q1 and Q3
    # --------------------------------------------------------

    route_stats = (
        df.groupby(
            "route",
            dropna=False
        )["total_fare"]
        .agg(
            q1=lambda x: x.quantile(0.25),
            q3=lambda x: x.quantile(0.75)
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Calculate IQR
    # --------------------------------------------------------

    route_stats["iqr"] = (
        route_stats["q3"]
        - route_stats["q1"]
    )

    # --------------------------------------------------------
    # Calculate bounds
    # --------------------------------------------------------

    route_stats["lower_bound"] = (
        route_stats["q1"]
        - 1.5 * route_stats["iqr"]
    )

    route_stats["upper_bound"] = (
        route_stats["q3"]
        + 1.5 * route_stats["iqr"]
    )

    # --------------------------------------------------------
    # Merge bounds back into dataset
    # --------------------------------------------------------

    df = df.merge(
        route_stats[
            [
                "route",
                "lower_bound",
                "upper_bound"
            ]
        ],
        on="route",
        how="left"
    )

    # --------------------------------------------------------
    # Flag outliers
    # --------------------------------------------------------

    df["fare_outlier"] = (

        (
            df["total_fare"]
            < df["lower_bound"]
        )

        |

        (
            df["total_fare"]
            > df["upper_bound"]
        )
    )

    # --------------------------------------------------------
    # Handle missing bounds
    # --------------------------------------------------------

    df["fare_outlier"] = (
        df["fare_outlier"]
        .fillna(False)
        .astype(bool)
    )

    # --------------------------------------------------------
    # Remove temporary columns
    # --------------------------------------------------------

    df = df.drop(
        columns=[
            "lower_bound",
            "upper_bound"
        ],
        errors="ignore"
    )

    logger.info(
        "Fare outliers flagged: %d",
        int(df["fare_outlier"].sum())
    )

    return df

# ============================================================
# MARKET FEATURES
# ============================================================

def create_market_features(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = df.copy()

    # Route average
    route_average = (
        df.groupby(
            "route"
        )[
            "total_fare"
        ]
        .transform(
            "mean"
        )
    )

    df[
        "route_average_fare"
    ] = route_average

    # Difference from route average
    df[
        "fare_vs_route_average_pct"
    ] = (

        (
            df[
                "total_fare"
            ]
            /
            df[
                "route_average_fare"
            ]
        )
        - 1
    ) * 100

    # Number of airlines competing on route
    df[
        "route_airline_count"
    ] = (
        df.groupby(
            "route"
        )[
            "airline"
        ]
        .transform(
            "nunique"
        )
    )

    # Route observation count
    df[
        "route_observation_count"
    ] = (
        df.groupby(
            "route"
        )[
            "record_id"
        ]
        .transform(
            "count"
        )
    )

    return df


# ============================================================
# FINAL COLUMN ORDER
# ============================================================

def organize_columns(
    df: pd.DataFrame
) -> pd.DataFrame:

    preferred = [

        "record_id",

        "search_id",

        "origin",

        "destination",

        "route",

        "outbound_date",

        "return_date",

        "collection_timestamp",

        "collection_date",

        "searched_at",

        "advance_purchase_days",

        "booking_window_category",

        "airline",

        "flight_type",

        "currency",

        "price",

        "total_fare",

        "base_fare",

        "taxes_fees",

        "stops",

        "total_duration_minutes",

        "departure_time",

        "arrival_time",

        "travel_class",

        "carbon_emissions_kg",

        "seats_available",

        "sold_out",

        "booking_token",

        "source",

        "source_engine",

        "travel_year",

        "travel_month",

        "travel_week",

        "travel_day",

        "travel_day_of_week",

        "travel_day_name",

        "travel_month_name",

        "is_weekend",

        "collection_hour",

        "fare_band",

        "log_fare",

        "fare_outlier",

        "route_average_fare",

        "fare_vs_route_average_pct",

        "route_airline_count",

        "route_observation_count",

        "search_currency",

        "search_timestamp",

        "search_request_id"
    ]

    existing = [
        column
        for column in preferred
        if column in df.columns
    ]

    remaining = [
        column
        for column in df.columns
        if column not in existing
    ]

    return df[
        existing + remaining
    ]


# ============================================================
# MAIN PROCESSOR
# ============================================================

def build_airfare_dataset():

    logger.info(
        "=" * 75
    )

    logger.info(
        "STARTING AIRFARE DATA PROCESSING"
    )

    logger.info(
        "=" * 75
    )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    searches = load_searches()

    options = load_flight_options()

    # --------------------------------------------------------
    # Join
    # --------------------------------------------------------

    df = join_search_metadata(
        searches,
        options
    )

    logger.info(
        "After search join: %d records",
        len(df)
    )

    # --------------------------------------------------------
    # Standardize
    # --------------------------------------------------------

    df = standardize_route_fields(
        df
    )

    # --------------------------------------------------------
    # Booking features
    # --------------------------------------------------------

    df = create_booking_features(
        df
    )

    # --------------------------------------------------------
    # Time features
    # --------------------------------------------------------

    df = create_time_features(
        df
    )

    # --------------------------------------------------------
    # Fare features
    # --------------------------------------------------------

    df = create_fare_features(
        df
    )

    # --------------------------------------------------------
    # Duplicate detection
    # --------------------------------------------------------

    df = remove_duplicate_observations(
        df
    )

    # --------------------------------------------------------
    # Deterministic ID
    # --------------------------------------------------------

    df = create_record_id(
        df
    )

    # --------------------------------------------------------
    # Outliers
    # --------------------------------------------------------

    df = create_outlier_features(
        df
    )

    # --------------------------------------------------------
    # Market features
    # --------------------------------------------------------

    df = create_market_features(
        df
    )

    # --------------------------------------------------------
    # Source metadata
    # --------------------------------------------------------

    df["source"] = "SerpApi"

    df["source_engine"] = (
        "Google Flights"
    )

    # --------------------------------------------------------
    # Make sure required final fields exist
    # --------------------------------------------------------

    optional_fields = [

        "base_fare",

        "taxes_fees",

        "departure_time",

        "arrival_time",

        "travel_class",

        "seats_available",

        "sold_out"
    ]

    for column in optional_fields:

        if column not in df.columns:

            df[column] = np.nan

    # --------------------------------------------------------
    # Final column organization
    # --------------------------------------------------------

    df = organize_columns(
        df
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    df = df.sort_values(
        [
            "collection_timestamp",
            "route",
            "outbound_date",
            "airline"
        ]
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # Save cleaned dataset
    # --------------------------------------------------------

    df.to_parquet(
        CLEANED_FILE,
        index=False
    )

    df.to_csv(
        CLEANED_CSV,
        index=False
    )

    # --------------------------------------------------------
    # Save processed dataset
    # --------------------------------------------------------

    # Analytical version
    processed = df.copy()

    processed.to_parquet(
        PROCESSED_FILE,
        index=False
    )

    processed.to_csv(
        PROCESSED_CSV,
        index=False
    )

    # --------------------------------------------------------
    # Final statistics
    # --------------------------------------------------------

    logger.info(
        ""
    )

    logger.info(
        "=" * 75
    )

    logger.info(
        "AIRFARE DATA PROCESSING COMPLETED"
    )

    logger.info(
        "=" * 75
    )

    logger.info(
        "Final records: %d",
        len(df)
    )

    logger.info(
        "Routes: %d",
        df["route"].nunique()
    )

    logger.info(
        "Airlines: %d",
        df["airline"].nunique()
    )

    logger.info(
        "Travel dates: %d",
        df["outbound_date"].nunique()
    )

    logger.info(
        "Average fare: %.2f",
        df["total_fare"].mean()
    )

    logger.info(
        "Minimum fare: %.2f",
        df["total_fare"].min()
    )

    logger.info(
        "Maximum fare: %.2f",
        df["total_fare"].max()
    )

    logger.info(
        "Cleaned output: %s",
        CLEANED_FILE
    )

    logger.info(
        "Processed output: %s",
        PROCESSED_FILE
    )

    logger.info(
        "=" * 75
    )

    return df


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    logging.basicConfig(

        level=logging.INFO,

        format=(
            "%(asctime)s - "
            "%(levelname)s - "
            "%(message)s"
        )
    )

    build_airfare_dataset()