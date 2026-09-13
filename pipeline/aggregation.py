import logging
import pandas as pd
import numpy as np


logger = logging.getLogger(__name__)


# ============================================================
# HELPER
# ============================================================

def add_percentage_change(
    df: pd.DataFrame,
    group_columns: list,
    value_column: str,
    output_column: str
) -> pd.DataFrame:

    if df.empty:
        return df

    df = df.copy()

    df[output_column] = (
        df.groupby(group_columns)[value_column]
        .pct_change()
        * 100
    )

    return df


# ============================================================
# DAILY AGGREGATION
# ============================================================

def daily_fare_analysis(
    df: pd.DataFrame
) -> pd.DataFrame:

    required = {
        "route",
        "outbound_date",
        "total_fare"
    }

    if not required.issubset(
        df.columns
    ):
        return pd.DataFrame()

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
        )
    )

    daily["fare_std"] = (
        daily["fare_std"]
        .fillna(0)
    )

    daily["fare_range"] = (
        daily["maximum_fare"]
        - daily["minimum_fare"]
    )

    daily["fare_volatility_pct"] = (
        daily["fare_std"]
        /
        daily["average_fare"]
        * 100
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
        ["route"],
        "average_fare",
        "daily_fare_change_pct"
    )

    return daily


# ============================================================
# WEEKLY AGGREGATION
# ============================================================

def weekly_fare_analysis(
    df: pd.DataFrame
) -> pd.DataFrame:

    if not {
        "outbound_date",
        "route",
        "total_fare"
    }.issubset(df.columns):

        return pd.DataFrame()

    temp = df.copy()

    temp["week_start"] = (
        temp["outbound_date"]
        - pd.to_timedelta(
            temp[
                "outbound_date"
            ].dt.dayofweek,
            unit="D"
        )
    )

    weekly = (
        temp.groupby(
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
            ),
            airlines=(
                "airline",
                "nunique"
            )
        )
    )

    weekly["fare_std"] = (
        weekly["fare_std"]
        .fillna(0)
    )

    weekly["fare_volatility_pct"] = (
        weekly["fare_std"]
        /
        weekly["average_fare"]
        * 100
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
        ["route"],
        "average_fare",
        "weekly_fare_change_pct"
    )

    return weekly


# ============================================================
# MONTHLY AGGREGATION
# ============================================================

def monthly_fare_analysis(
    df: pd.DataFrame
) -> pd.DataFrame:

    if not {
        "outbound_date",
        "route",
        "total_fare"
    }.issubset(df.columns):

        return pd.DataFrame()

    temp = df.copy()

    temp["month"] = (
        temp[
            "outbound_date"
        ].dt.to_period("M")
        .astype(str)
    )

    monthly = (
        temp.groupby(
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
            ),
            airlines=(
                "airline",
                "nunique"
            )
        )
    )

    monthly["fare_std"] = (
        monthly["fare_std"]
        .fillna(0)
    )

    monthly["fare_volatility_pct"] = (
        monthly["fare_std"]
        /
        monthly["average_fare"]
        * 100
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
        ["route"],
        "average_fare",
        "monthly_fare_change_pct"
    )

    return monthly


# ============================================================
# ROUTE-WISE ANALYSIS
# ============================================================

def route_analysis(
    df: pd.DataFrame
) -> pd.DataFrame:

    if not {
        "route",
        "total_fare"
    }.issubset(df.columns):

        return pd.DataFrame()

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
            ),
            average_duration_minutes=(
                "duration_minutes",
                "mean"
            ),
            average_stops=(
                "stops",
                "mean"
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
        * 100
    ).replace(
        [np.inf, -np.inf],
        np.nan
    ).fillna(0)

    return route.sort_values(
        "average_fare",
        ascending=False
    )


# ============================================================
# AIRLINE ANALYSIS
# ============================================================

def airline_analysis(
    df: pd.DataFrame
) -> pd.DataFrame:

    if not {
        "airline",
        "route",
        "total_fare"
    }.issubset(df.columns):

        return pd.DataFrame()

    airline = (
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
                "duration_minutes",
                "mean"
            ),
            average_stops=(
                "stops",
                "mean"
            )
        )
    )

    return airline.sort_values(
        [
            "route",
            "average_fare"
        ]
    )


# ============================================================
# BOOKING WINDOW ANALYSIS
# ============================================================

def booking_window_analysis(
    df: pd.DataFrame
) -> pd.DataFrame:

    required = {
        "route",
        "advance_purchase_days",
        "total_fare"
    }

    if not required.issubset(
        df.columns
    ):
        return pd.DataFrame()

    result = (
        df.groupby(
            [
                "route",
                "booking_window_category"
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
            )
        )
    )

    return result


# ============================================================
# WEEKDAY / WEEKEND ANALYSIS
# ============================================================

def weekday_weekend_analysis(
    df: pd.DataFrame
) -> pd.DataFrame:

    if not {
        "route",
        "is_weekend",
        "total_fare"
    }.issubset(df.columns):

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
        result["is_weekend"],
        "Weekend",
        "Weekday"
    )

    return result


# ============================================================
# APIx INPUT
# ============================================================

def create_api_x_input(
    df: pd.DataFrame
) -> pd.DataFrame:

    if not {
        "route",
        "outbound_date",
        "total_fare"
    }.issubset(df.columns):

        return pd.DataFrame()

    result = (
        df.groupby(
            [
                "outbound_date",
                "route"
            ],
            as_index=False
        )
        .agg(
            current_average_fare=(
                "total_fare",
                "mean"
            ),
            current_median_fare=(
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
            sample_size=(
                "total_fare",
                "count"
            ),
            airlines=(
                "airline",
                "nunique"
            )
        )
    )

    result["fare_std"] = (
        result["fare_std"]
        .fillna(0)
    )

    result[
        "fare_volatility_pct"
    ] = (

        result["fare_std"]
        /
        result["current_average_fare"]
        * 100

    ).replace(
        [np.inf, -np.inf],
        np.nan
    ).fillna(0)

    return result


# ============================================================
# RUN ALL ANALYSIS
# ============================================================

def run_all_aggregations(
    df: pd.DataFrame
) -> dict:

    return {

        "daily":
            daily_fare_analysis(df),

        "weekly":
            weekly_fare_analysis(df),

        "monthly":
            monthly_fare_analysis(df),

        "route":
            route_analysis(df),

        "airline":
            airline_analysis(df),

        "booking_window":
            booking_window_analysis(df),

        "weekday_weekend":
            weekday_weekend_analysis(df),

        "api_x":
            create_api_x_input(df)
    }