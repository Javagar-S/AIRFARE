import logging
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

logger = logging.getLogger(__name__)

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DATA_DIR = PROJECT_ROOT / "data"

PROCESSED_DIR = DATA_DIR / "processed"

ANALYTICS_DIR = DATA_DIR / "analytics"

API_X_DIR = ANALYTICS_DIR / "api_x"


ANALYTICS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

API_X_DIR.mkdir(
    parents=True,
    exist_ok=True
)


INPUT_FILE = (
    PROCESSED_DIR
    / "airfare_preprocessed.parquet"
)


# ============================================================
# ROUTE WEIGHTS
# ============================================================
#
# Prototype weights.
#
# IMPORTANT:
# These are NOT official CPI weights.
# Replace them later with validated weights from the
# methodology/reference source used by your team.
# ============================================================

DEFAULT_ROUTE_WEIGHTS = {

    "DEL-BOM": 0.30,

    "BLR-DEL": 0.25,

    "BLR-BOM": 0.20,

    "DEL-HYD": 0.15,

    "BOM-HYD": 0.10
}


# ============================================================
# LOAD DATA
# ============================================================

def load_dataset() -> pd.DataFrame:
    """
    Load the processed analytical dataset.
    """

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Processed dataset not found:\n"
            f"{INPUT_FILE}\n\n"
            f"Run data_processor.py first."
        )

    logger.info(
        "Loading processed dataset: %s",
        INPUT_FILE
    )

    df = pd.read_parquet(
        INPUT_FILE
    )

    logger.info(
        "Loaded records: %d",
        len(df)
    )

    return df


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Standardize important analytical columns.
    """

    df = df.copy()

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    for column in [
        "collection_timestamp",
        "collection_date",
        "outbound_date",
        "return_date"
    ]:

        if column in df.columns:

            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )

    # --------------------------------------------------------
    # Numeric
    # --------------------------------------------------------

    for column in [
        "total_fare",
        "price",
        "advance_purchase_days",
        "duration_minutes",
        "total_duration_minutes",
        "stops",
        "carbon_emissions_kg"
    ]:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # --------------------------------------------------------
    # Fare column normalization
    # --------------------------------------------------------

    if "total_fare" not in df.columns:

        if "price" in df.columns:

            df["total_fare"] = df["price"]

    # --------------------------------------------------------
    # Route
    # --------------------------------------------------------

    if "route" not in df.columns:

        if {
            "origin",
            "destination"
        }.issubset(df.columns):

            df["route"] = (

                df["origin"]
                .astype(str)
                .str.upper()
                .str.strip()

                + "-"

                + df["destination"]
                .astype(str)
                .str.upper()
                .str.strip()
            )

    return df


# ============================================================
# VALIDATION
# ============================================================

def validate_dataset(
    df: pd.DataFrame
) -> pd.DataFrame:

    required = [
        "route",
        "outbound_date",
        "total_fare"
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "Missing analytical columns: "
            + ", ".join(missing)
        )

    before = len(df)

    df = df.dropna(
        subset=required
    )

    df = df[
        df["total_fare"] > 0
    ]

    logger.info(
        "Valid analytical records: %d",
        len(df)
    )

    logger.info(
        "Records excluded during validation: %d",
        before - len(df)
    )

    return df.reset_index(
        drop=True
    )


# ============================================================
# HELPER
# ============================================================

def add_percentage_change(
    df: pd.DataFrame,
    value_column: str,
    group_column=None,
    output_column="change_pct"
) -> pd.DataFrame:

    df = df.copy()

    if group_column is None:

        previous = (
            df[value_column]
            .shift(1)
        )

    else:

        previous = (
            df.groupby(
                group_column
            )[value_column]
            .shift(1)
        )

    df[output_column] = (

        (
            df[value_column]
            /
            previous
        )
        - 1
    ) * 100

    df[output_column] = (
        df[output_column]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
    )

    return df


# ============================================================
# DAILY FARE ANALYSIS
# ============================================================

def build_daily_fare(
    df: pd.DataFrame
) -> pd.DataFrame:

    daily = (
        df.groupby(
            [
                "outbound_date",
                "route"
            ],
            as_index=False
        )
        .agg(

            average_fare=(
                "total_fare",
                "mean"
            ),

            median_fare=(
                "total_fare",
                "median"
            ),

            minimum_fare=(
                "total_fare",
                "min"
            ),

            maximum_fare=(
                "total_fare",
                "max"
            ),

            fare_std=(
                "total_fare",
                "std"
            ),

            observations=(
                "total_fare",
                "count"
            ),

            airlines=(
                "airline",
                "nunique"
            )
            if "airline"
            in df.columns
            else (
                "total_fare",
                "count"
            )
        )
    )

    daily["fare_std"] = (
        daily["fare_std"]
        .fillna(0)
    )

    daily["fare_range"] = (
        daily["maximum_fare"]
        -
        daily["minimum_fare"]
    )

    daily["volatility_pct"] = (

        daily["fare_std"]
        /
        daily["average_fare"]
        *
        100

    ).replace(
        [np.inf, -np.inf],
        np.nan
    ).fillna(0)

    daily = daily.sort_values(
        [
            "route",
            "outbound_date"
        ]
    )

    daily = add_percentage_change(
        daily,
        "average_fare",
        "route",
        "fare_change_pct"
    )

    return daily


# ============================================================
# WEEKLY FARE ANALYSIS
# ============================================================

def build_weekly_fare(
    df: pd.DataFrame
) -> pd.DataFrame:

    data = df.copy()

    data["week_start"] = (

        data[
            "outbound_date"
        ]
        -
        pd.to_timedelta(
            data[
                "outbound_date"
            ].dt.dayofweek,
            unit="D"
        )
    )

    weekly = (
        data.groupby(
            [
                "week_start",
                "route"
            ],
            as_index=False
        )
        .agg(

            average_fare=(
                "total_fare",
                "mean"
            ),

            median_fare=(
                "total_fare",
                "median"
            ),

            minimum_fare=(
                "total_fare",
                "min"
            ),

            maximum_fare=(
                "total_fare",
                "max"
            ),

            fare_std=(
                "total_fare",
                "std"
            ),

            observations=(
                "total_fare",
                "count"
            )
        )
    )

    weekly["fare_std"] = (
        weekly["fare_std"]
        .fillna(0)
    )

    weekly["volatility_pct"] = (

        weekly["fare_std"]
        /
        weekly["average_fare"]
        *
        100

    ).replace(
        [np.inf, -np.inf],
        np.nan
    ).fillna(0)

    weekly = weekly.sort_values(
        [
            "route",
            "week_start"
        ]
    )

    weekly = add_percentage_change(
        weekly,
        "average_fare",
        "route",
        "fare_change_pct"
    )

    return weekly


# ============================================================
# MONTHLY FARE ANALYSIS
# ============================================================

def build_monthly_fare(
    df: pd.DataFrame
) -> pd.DataFrame:

    data = df.copy()

    data["month"] = (
        data[
            "outbound_date"
        ]
        .dt
        .to_period("M")
        .astype(str)
    )

    monthly = (
        data.groupby(
            [
                "month",
                "route"
            ],
            as_index=False
        )
        .agg(

            average_fare=(
                "total_fare",
                "mean"
            ),

            median_fare=(
                "total_fare",
                "median"
            ),

            minimum_fare=(
                "total_fare",
                "min"
            ),

            maximum_fare=(
                "total_fare",
                "max"
            ),

            fare_std=(
                "total_fare",
                "std"
            ),

            observations=(
                "total_fare",
                "count"
            )
        )
    )

    monthly["fare_std"] = (
        monthly["fare_std"]
        .fillna(0)
    )

    monthly["volatility_pct"] = (

        monthly["fare_std"]
        /
        monthly["average_fare"]
        *
        100

    ).replace(
        [np.inf, -np.inf],
        np.nan
    ).fillna(0)

    monthly = monthly.sort_values(
        [
            "route",
            "month"
        ]
    )

    monthly = add_percentage_change(
        monthly,
        "average_fare",
        "route",
        "fare_change_pct"
    )

    return monthly


# ============================================================
# ROUTE ANALYSIS
# ============================================================

def build_route_analysis(
    df: pd.DataFrame
) -> pd.DataFrame:

    route = (
        df.groupby(
            "route",
            as_index=False
        )
        .agg(

            average_fare=(
                "total_fare",
                "mean"
            ),

            median_fare=(
                "total_fare",
                "median"
            ),

            minimum_fare=(
                "total_fare",
                "min"
            ),

            maximum_fare=(
                "total_fare",
                "max"
            ),

            fare_std=(
                "total_fare",
                "std"
            ),

            observations=(
                "total_fare",
                "count"
            ),

            airlines=(
                "airline",
                "nunique"
            )
            if "airline"
            in df.columns
            else (
                "total_fare",
                "count"
            )
        )
    )

    route["fare_std"] = (
        route["fare_std"]
        .fillna(0)
    )

    route["volatility_pct"] = (

        route["fare_std"]
        /
        route["average_fare"]
        *
        100

    ).replace(
        [np.inf, -np.inf],
        np.nan
    ).fillna(0)

    route["fare_range"] = (
        route["maximum_fare"]
        -
        route["minimum_fare"]
    )

    route["rank_by_average_fare"] = (
        route[
            "average_fare"
        ]
        .rank(
            ascending=False,
            method="dense"
        )
        .astype(int)
    )

    return route.sort_values(
        "average_fare",
        ascending=False
    )


# ============================================================
# AIRLINE ANALYSIS
# ============================================================

def build_airline_analysis(
    df: pd.DataFrame
) -> pd.DataFrame:

    if "airline" not in df.columns:

        return pd.DataFrame()

    result = (
        df.groupby(
            [
                "route",
                "airline"
            ],
            as_index=False
        )
        .agg(

            average_fare=(
                "total_fare",
                "mean"
            ),

            median_fare=(
                "total_fare",
                "median"
            ),

            minimum_fare=(
                "total_fare",
                "min"
            ),

            maximum_fare=(
                "total_fare",
                "max"
            ),

            observations=(
                "total_fare",
                "count"
            ),

            average_duration_minutes=(
                "total_duration_minutes",
                "mean"
            )
            if "total_duration_minutes"
            in df.columns
            else (
                "total_fare",
                "mean"
            ),

            average_stops=(
                "stops",
                "mean"
            )
            if "stops"
            in df.columns
            else (
                "total_fare",
                "mean"
            )
        )
    )

    return result.sort_values(
        [
            "route",
            "average_fare"
        ]
    )


# ============================================================
# BOOKING WINDOW ANALYSIS
# ============================================================

def build_booking_window_analysis(
    df: pd.DataFrame
) -> pd.DataFrame:

    if (
        "advance_purchase_days"
        not in df.columns
    ):

        return pd.DataFrame()

    data = df.copy()

    data[
        "booking_window"
    ] = pd.cut(

        data[
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

    result = (
        data.groupby(
            [
                "route",
                "booking_window"
            ],
            observed=True,
            as_index=False
        )
        .agg(

            average_fare=(
                "total_fare",
                "mean"
            ),

            median_fare=(
                "total_fare",
                "median"
            ),

            minimum_fare=(
                "total_fare",
                "min"
            ),

            maximum_fare=(
                "total_fare",
                "max"
            ),

            observations=(
                "total_fare",
                "count"
            )
        )
    )

    order = [
        "60+ days",
        "31-60 days",
        "15-30 days",
        "8-14 days",
        "4-7 days",
        "0-3 days"
    ]

    result[
        "sort_order"
    ] = result[
        "booking_window"
    ].astype(str).map(
        {
            value: index
            for index, value
            in enumerate(order)
        }
    )

    result = (
        result
        .sort_values(
            [
                "route",
                "sort_order"
            ]
        )
        .drop(
            columns=[
                "sort_order"
            ]
        )
    )

    return result


# ============================================================
# WEEKDAY / WEEKEND
# ============================================================

def build_weekday_weekend_analysis(
    df: pd.DataFrame
) -> pd.DataFrame:

    if "is_weekend" not in df.columns:

        return pd.DataFrame()

    result = (
        df.groupby(
            [
                "route",
                "is_weekend"
            ],
            as_index=False
        )
        .agg(

            average_fare=(
                "total_fare",
                "mean"
            ),

            median_fare=(
                "total_fare",
                "median"
            ),

            observations=(
                "total_fare",
                "count"
            )
        )
    )

    result[
        "day_type"
    ] = np.where(

        result[
            "is_weekend"
        ],

        "Weekend",

        "Weekday"
    )

    return result


# ============================================================
# FARE DISTRIBUTION
# ============================================================

def build_fare_distribution(
    df: pd.DataFrame
) -> pd.DataFrame:

    data = df.copy()

    data[
        "fare_bucket"
    ] = pd.cut(

        data[
            "total_fare"
        ],

        bins=[
            0,
            5000,
            7500,
            10000,
            15000,
            25000,
            50000,
            np.inf
        ],

        labels=[
            "<=5K",
            "5K-7.5K",
            "7.5K-10K",
            "10K-15K",
            "15K-25K",
            "25K-50K",
            "50K+"
        ]
    )

    result = (
        data.groupby(
            "fare_bucket",
            observed=True,
            as_index=False
        )
        .agg(
            observations=(
                "total_fare",
                "count"
            )
        )
    )

    return result


# ============================================================
# APIx WEIGHT VALIDATION
# ============================================================

def normalize_route_weights(
    route_weights
) -> dict:

    total = sum(
        route_weights.values()
    )

    if total <= 0:

        raise ValueError(
            "Route weights must sum to > 0."
        )

    return {
        route:
            weight / total

        for route, weight
        in route_weights.items()
    }


# ============================================================
# ROUTE BASE FARES
# ============================================================

def calculate_base_fares(
    df: pd.DataFrame,
    base_date: pd.Timestamp
) -> pd.DataFrame:

    base_data = df[
        df[
            "outbound_date"
        ]
        == base_date
    ]

    if base_data.empty:

        return pd.DataFrame(
            columns=[
                "route",
                "base_fare"
            ]
        )

    return (
        base_data.groupby(
            "route",
            as_index=False
        )[
            "total_fare"
        ]
        .mean()
        .rename(
            columns={
                "total_fare":
                    "base_fare"
            }
        )
    )


# ============================================================
# APIx ROUTE INDEX
# ============================================================

def build_route_api_x(
    df: pd.DataFrame,
    route_weights=None
) -> pd.DataFrame:

    data = df.copy()

    if route_weights is None:

        route_weights = (
            DEFAULT_ROUTE_WEIGHTS
        )

    route_weights = normalize_route_weights(
        route_weights
    )

    # --------------------------------------------------------
    # Base date
    # --------------------------------------------------------

    base_date = (
        data[
            "outbound_date"
        ].min()
    )

    logger.info(
        "APIx base date: %s",
        base_date.date()
    )

    # --------------------------------------------------------
    # Base fare per route
    # --------------------------------------------------------

    base_fares = calculate_base_fares(
        data,
        base_date
    )

    if base_fares.empty:

        logger.warning(
            "Could not calculate base fares."
        )

        return pd.DataFrame()

    # --------------------------------------------------------
    # Daily route fare
    # --------------------------------------------------------

    daily = (
        data.groupby(
            [
                "outbound_date",
                "route"
            ],
            as_index=False
        )[
            "total_fare"
        ]
        .mean()
        .rename(
            columns={
                "total_fare":
                    "average_fare"
            }
        )
    )

    # --------------------------------------------------------
    # Merge base
    # --------------------------------------------------------

    daily = daily.merge(
        base_fares,
        on="route",
        how="left"
    )

    # --------------------------------------------------------
    # Route index
    # --------------------------------------------------------

    daily[
        "route_index"
    ] = (

        daily[
            "average_fare"
        ]
        /
        daily[
            "base_fare"
        ]
        *
        100
    )

    # --------------------------------------------------------
    # Weight
    # --------------------------------------------------------

    daily[
        "route_weight"
    ] = (
        daily[
            "route"
        ]
        .map(
            route_weights
        )
        .fillna(0)
    )

    daily[
        "weighted_contribution"
    ] = (

        daily[
            "route_index"
        ]
        *
        daily[
            "route_weight"
        ]
    )

    return daily.sort_values(
        [
            "outbound_date",
            "route"
        ]
    )


# ============================================================
# OVERALL APIx
# ============================================================

def build_daily_api_x(
    route_api_x: pd.DataFrame
) -> pd.DataFrame:

    if route_api_x.empty:

        return pd.DataFrame()

    result = (
        route_api_x.groupby(
            "outbound_date",
            as_index=False
        )
        .agg(

            weighted_index=(
                "weighted_contribution",
                "sum"
            ),

            available_weight=(
                "route_weight",
                "sum"
            ),

            route_count=(
                "route",
                "nunique"
            )
        )
    )

    result[
        "api_x"
    ] = np.where(

        result[
            "available_weight"
        ] > 0,

        result[
            "weighted_index"
        ]
        /
        result[
            "available_weight"
        ],

        np.nan
    )

    result[
        "api_x"
    ] = (
        result[
            "api_x"
        ]
        .round(2)
    )

    result = result.sort_values(
        "outbound_date"
    )

    result = add_percentage_change(
        result,
        "api_x",
        None,
        "api_x_change_pct"
    )

    return result


# ============================================================
# WEEKLY APIx
# ============================================================

def build_weekly_api_x(
    daily_api_x: pd.DataFrame
) -> pd.DataFrame:

    if daily_api_x.empty:

        return pd.DataFrame()

    data = daily_api_x.copy()

    data["week_start"] = (

        data[
            "outbound_date"
        ]
        -
        pd.to_timedelta(
            data[
                "outbound_date"
            ].dt.dayofweek,
            unit="D"
        )
    )

    weekly = (
        data.groupby(
            "week_start",
            as_index=False
        )
        .agg(

            api_x=(
                "api_x",
                "mean"
            ),

            observations=(
                "route_count",
                "sum"
            )
        )
    )

    weekly = weekly.sort_values(
        "week_start"
    )

    weekly = add_percentage_change(
        weekly,
        "api_x",
        None,
        "api_x_change_pct"
    )

    return weekly


# ============================================================
# MONTHLY APIx
# ============================================================

def build_monthly_api_x(
    daily_api_x: pd.DataFrame
) -> pd.DataFrame:

    if daily_api_x.empty:

        return pd.DataFrame()

    data = daily_api_x.copy()

    data["month"] = (
        data[
            "outbound_date"
        ]
        .dt
        .to_period("M")
        .astype(str)
    )

    monthly = (
        data.groupby(
            "month",
            as_index=False
        )
        .agg(

            api_x=(
                "api_x",
                "mean"
            ),

            observations=(
                "route_count",
                "sum"
            )
        )
    )

    return monthly


# ============================================================
# NATIONAL SNAPSHOT
# ============================================================

def build_national_snapshot(
    df: pd.DataFrame,
    daily_api_x: pd.DataFrame,
    route_analysis: pd.DataFrame
) -> pd.DataFrame:

    if df.empty:

        return pd.DataFrame()

    average_fare = float(
        df[
            "total_fare"
        ].mean()
    )

    minimum_fare = float(
        df[
            "total_fare"
        ].min()
    )

    maximum_fare = float(
        df[
            "total_fare"
        ].max()
    )

    api_x = None

    api_x_change = None

    if not daily_api_x.empty:

        api_x = float(
            daily_api_x.iloc[-1][
                "api_x"
            ]
        )

        if (
            len(daily_api_x)
            >= 2
        ):

            previous = float(
                daily_api_x.iloc[-2][
                    "api_x"
                ]
            )

            if previous != 0:

                api_x_change = (
                    (
                        api_x
                        -
                        previous
                    )
                    /
                    previous
                    *
                    100
                )

    highest_route = None

    lowest_route = None

    if not route_analysis.empty:

        highest_route = (
            route_analysis.iloc[0][
                "route"
            ]
        )

        lowest_route = (
            route_analysis
            .sort_values(
                "average_fare"
            )
            .iloc[0][
                "route"
            ]
        )

    snapshot = pd.DataFrame(
        [
            {

                "generated_at":
                    pd.Timestamp.utcnow(),

                "api_x":
                    api_x,

                "api_x_change_pct":
                    api_x_change,

                "average_fare":
                    average_fare,

                "minimum_fare":
                    minimum_fare,

                "maximum_fare":
                    maximum_fare,

                "routes":
                    int(
                        df[
                            "route"
                        ].nunique()
                    ),

                "airlines":
                    int(
                        df[
                            "airline"
                        ].nunique()
                    )
                    if "airline"
                    in df.columns
                    else 0,

                "observations":
                    int(len(df)),

                "travel_dates":
                    int(
                        df[
                            "outbound_date"
                        ].nunique()
                    ),

                "highest_average_fare_route":
                    highest_route,

                "lowest_average_fare_route":
                    lowest_route
            }
        ]
    )

    return snapshot


# ============================================================
# WRITE OUTPUT
# ============================================================

def save_output(
    df: pd.DataFrame,
    filename: str,
    directory: Path = ANALYTICS_DIR
):

    if df.empty:

        logger.warning(
            "Skipping empty output: %s",
            filename
        )

        return

    directory.mkdir(
        parents=True,
        exist_ok=True
    )

    csv_path = (
        directory
        / f"{filename}.csv"
    )

    parquet_path = (
        directory
        / f"{filename}.parquet"
    )

    df.to_csv(
        csv_path,
        index=False
    )

    df.to_parquet(
        parquet_path,
        index=False
    )

    logger.info(
        "Saved %s | rows=%d",
        filename,
        len(df)
    )


# ============================================================
# MAIN ANALYTICS ENGINE
# ============================================================

def run_analytics():

    logger.info(
        "=" * 80
    )

    logger.info(
        "INDIA AIRFARE ANALYTICS ENGINE"
    )

    logger.info(
        "=" * 80
    )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = load_dataset()

    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    df = prepare_data(
        df
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    df = validate_dataset(
        df
    )

    # --------------------------------------------------------
    # Standard analytics
    # --------------------------------------------------------

    daily = build_daily_fare(
        df
    )

    weekly = build_weekly_fare(
        df
    )

    monthly = build_monthly_fare(
        df
    )

    routes = build_route_analysis(
        df
    )

    airlines = build_airline_analysis(
        df
    )

    booking = (
        build_booking_window_analysis(
            df
        )
    )

    weekday_weekend = (
        build_weekday_weekend_analysis(
            df
        )
    )

    fare_distribution = (
        build_fare_distribution(
            df
        )
    )

    # --------------------------------------------------------
    # APIx
    # --------------------------------------------------------

    route_api_x = (
        build_route_api_x(
            df
        )
    )

    daily_api_x = (
        build_daily_api_x(
            route_api_x
        )
    )

    weekly_api_x = (
        build_weekly_api_x(
            daily_api_x
        )
    )

    monthly_api_x = (
        build_monthly_api_x(
            daily_api_x
        )
    )

    # --------------------------------------------------------
    # Snapshot
    # --------------------------------------------------------

    snapshot = (
        build_national_snapshot(

            df,

            daily_api_x,

            routes
        )
    )

    # --------------------------------------------------------
    # Save standard analytics
    # --------------------------------------------------------

    save_output(
        daily,
        "daily_fare"
    )

    save_output(
        weekly,
        "weekly_fare"
    )

    save_output(
        monthly,
        "monthly_fare"
    )

    save_output(
        routes,
        "route_analysis"
    )

    save_output(
        airlines,
        "airline_analysis"
    )

    save_output(
        booking,
        "booking_window_analysis"
    )

    save_output(
        weekday_weekend,
        "weekday_weekend_analysis"
    )

    save_output(
        fare_distribution,
        "fare_distribution"
    )

    save_output(
        snapshot,
        "national_snapshot"
    )

    # --------------------------------------------------------
    # Save APIx
    # --------------------------------------------------------

    save_output(
        route_api_x,
        "daily_route_api_x",
        API_X_DIR
    )

    save_output(
        daily_api_x,
        "daily_api_x",
        API_X_DIR
    )

    save_output(
        weekly_api_x,
        "weekly_api_x",
        API_X_DIR
    )

    save_output(
        monthly_api_x,
        "monthly_api_x",
        API_X_DIR
    )

    # --------------------------------------------------------
    # Console summary
    # --------------------------------------------------------

    logger.info(
        ""
    )

    logger.info(
        "ANALYTICS SUMMARY"
    )

    logger.info(
        "Records: %d",
        len(df)
    )

    logger.info(
        "Routes: %d",
        df["route"].nunique()
    )

    logger.info(
        "Airlines: %d",
        df["airline"].nunique()
        if "airline" in df.columns
        else 0
    )

    logger.info(
        "Travel dates: %d",
        df["outbound_date"].nunique()
    )

    logger.info(
        "Daily rows: %d",
        len(daily)
    )

    logger.info(
        "Weekly rows: %d",
        len(weekly)
    )

    logger.info(
        "Monthly rows: %d",
        len(monthly)
    )

    logger.info(
        "APIx rows: %d",
        len(daily_api_x)
    )

    if not daily_api_x.empty:

        logger.info(
            "Latest APIx: %.2f",
            daily_api_x.iloc[-1][
                "api_x"
            ]
        )

    logger.info(
        ""
    )

    logger.info(
        "=" * 80
    )

    logger.info(
        "ANALYTICS ENGINE COMPLETED"
    )

    logger.info(
        "=" * 80
    )

    return {

        "data":
            df,

        "daily":
            daily,

        "weekly":
            weekly,

        "monthly":
            monthly,

        "routes":
            routes,

        "airlines":
            airlines,

        "booking":
            booking,

        "weekday_weekend":
            weekday_weekend,

        "fare_distribution":
            fare_distribution,

        "route_api_x":
            route_api_x,

        "daily_api_x":
            daily_api_x,

        "weekly_api_x":
            weekly_api_x,

        "monthly_api_x":
            monthly_api_x,

        "snapshot":
            snapshot
    }


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

    try:

        run_analytics()

    except Exception as exc:

        logger.exception(
            "Analytics engine failed: %s",
            exc
        )

        raise