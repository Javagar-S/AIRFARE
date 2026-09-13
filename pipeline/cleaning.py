import logging
import pandas as pd
import numpy as np


logger = logging.getLogger(__name__)


# ============================================================
# EXPECTED COLUMNS
# ============================================================

EXPECTED_COLUMNS = [

    "record_id",

    "collection_timestamp",

    "source",

    "source_engine",

    "departure_airport",

    "arrival_airport",

    "route",

    "outbound_date",

    "return_date",

    "advance_purchase_days",

    "airline",

    "flight_numbers",

    "departure_time",

    "arrival_time",

    "duration_minutes",

    "stops",

    "travel_class",

    "base_fare",

    "taxes_fees",

    "total_fare",

    "price",

    "currency",

    "seats_available",

    "sold_out",

    "availability_details"
]


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text_columns(
    df: pd.DataFrame
) -> pd.DataFrame:

    text_columns = [

        "source",

        "source_engine",

        "departure_airport",

        "arrival_airport",

        "route",

        "airline",

        "travel_class",

        "currency"
    ]

    for column in text_columns:

        if column in df.columns:

            df[column] = (

                df[column]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.replace(
                    r"\s+",
                    " ",
                    regex=True
                )
            )

    return df


# ============================================================
# DATE CLEANING
# ============================================================

def clean_date_columns(
    df: pd.DataFrame
) -> pd.DataFrame:

    date_columns = [

        "collection_timestamp",

        "outbound_date",

        "return_date"
    ]

    for column in date_columns:

        if column in df.columns:

            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )

    return df


# ============================================================
# NUMERIC CLEANING
# ============================================================

def clean_numeric_columns(
    df: pd.DataFrame
) -> pd.DataFrame:

    numeric_columns = [

        "advance_purchase_days",

        "duration_minutes",

        "stops",

        "base_fare",

        "taxes_fees",

        "total_fare",

        "price",

        "seats_available"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


# ============================================================
# NORMALIZE AIRPORT CODES
# ============================================================

def normalize_airports(
    df: pd.DataFrame
) -> pd.DataFrame:

    for column in [

        "departure_airport",

        "arrival_airport"
    ]:

        if column in df.columns:

            df[column] = (

                df[column]
                .fillna("")
                .astype(str)
                .str.upper()
                .str.strip()
            )

    return df


# ============================================================
# NORMALIZE AIRLINE
# ============================================================

def normalize_airlines(
    df: pd.DataFrame
) -> pd.DataFrame:

    if "airline" in df.columns:

        df["airline"] = (

            df["airline"]
            .fillna("UNKNOWN")
            .astype(str)
            .str.strip()
        )

        df.loc[
            df["airline"] == "",
            "airline"
        ] = "UNKNOWN"

    return df


# ============================================================
# CREATE / REBUILD ROUTE
# ============================================================

def create_route(
    df: pd.DataFrame
) -> pd.DataFrame:

    if {
        "departure_airport",
        "arrival_airport"
    }.issubset(df.columns):

        df["route"] = (

            df["departure_airport"]
            + "-"
            + df["arrival_airport"]
        )

    return df


# ============================================================
# FARE VALIDATION
# ============================================================

def validate_fares(
    df: pd.DataFrame
) -> pd.DataFrame:

    if "total_fare" in df.columns:

        # Negative or zero fares are invalid
        df.loc[
            df["total_fare"] <= 0,
            "total_fare"
        ] = np.nan

    if "price" in df.columns:

        df.loc[
            df["price"] <= 0,
            "price"
        ] = np.nan

    return df


# ============================================================
# MISSING VALUE HANDLING
# ============================================================

def handle_missing_values(
    df: pd.DataFrame
) -> pd.DataFrame:

    # Critical columns
    critical_columns = [

        "record_id",

        "departure_airport",

        "arrival_airport",

        "outbound_date",

        "airline",

        "total_fare"
    ]

    existing_critical = [

        c
        for c in critical_columns
        if c in df.columns
    ]

    df = df.dropna(
        subset=existing_critical
    )

    # Optional numerical features
    if "duration_minutes" in df.columns:

        df["duration_minutes"] = (

            df["duration_minutes"]
            .fillna(
                df["duration_minutes"].median()
            )
        )

    if "stops" in df.columns:

        df["stops"] = (
            df["stops"]
            .fillna(0)
            .astype(int)
        )

    if "advance_purchase_days" in df.columns:

        df["advance_purchase_days"] = (

            df["advance_purchase_days"]
            .fillna(0)
            .astype(int)
        )

    if "currency" in df.columns:

        df["currency"] = (

            df["currency"]
            .replace(
                "",
                np.nan
            )
            .fillna("INR")
        )

    return df


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(
    df: pd.DataFrame
) -> pd.DataFrame:

    before = len(df)

    if "record_id" in df.columns:

        df = df.drop_duplicates(
            subset=["record_id"],
            keep="last"
        )

    else:

        duplicate_columns = [

            "departure_airport",

            "arrival_airport",

            "outbound_date",

            "airline",

            "price",

            "departure_time"
        ]

        existing = [

            c
            for c in duplicate_columns
            if c in df.columns
        ]

        df = df.drop_duplicates(
            subset=existing,
            keep="last"
        )

    after = len(df)

    logger.info(
        "Duplicate rows removed: %d",
        before - after
    )

    return df


# ============================================================
# OUTLIER FLAGGING
# ============================================================

def add_fare_outlier_flag(
    df: pd.DataFrame
) -> pd.DataFrame:

    if "total_fare" not in df.columns:

        return df

    # Use IQR within the dataset.
    q1 = df[
        "total_fare"
    ].quantile(0.25)

    q3 = df[
        "total_fare"
    ].quantile(0.75)

    iqr = q3 - q1

    lower = max(
        0,
        q1 - 1.5 * iqr
    )

    upper = (
        q3
        + 1.5 * iqr
    )

    df["fare_outlier"] = (

        (df["total_fare"] < lower)
        |
        (df["total_fare"] > upper)
    )

    return df


# ============================================================
# MAIN CLEANING FUNCTION
# ============================================================

def clean_dataset(
    df: pd.DataFrame
) -> pd.DataFrame:

    if df.empty:

        return df

    logger.info(
        "Starting cleaning: %d rows",
        len(df)
    )

    df = df.copy()

    df = clean_text_columns(df)

    df = clean_date_columns(df)

    df = clean_numeric_columns(df)

    df = normalize_airports(df)

    df = normalize_airlines(df)

    df = create_route(df)

    df = validate_fares(df)

    df = remove_duplicates(df)

    df = handle_missing_values(df)

    df = add_fare_outlier_flag(df)

    # Sort chronologically
    if "collection_timestamp" in df.columns:

        df = df.sort_values(
            "collection_timestamp"
        )

    df = df.reset_index(
        drop=True
    )

    logger.info(
        "Cleaning completed: %d rows",
        len(df)
    )

    return df