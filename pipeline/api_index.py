import logging
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd


logger = logging.getLogger(__name__)


# ============================================================
# DEFAULT ROUTE WEIGHTS
# ============================================================
#
# IMPORTANT:
# These are PROTOTYPE weights.
#
# For the final SIH implementation, replace them with
# defensible weights derived from the chosen reference source /
# CPI-aligned methodology.
#
# The weights must sum to 1.0
# ============================================================

DEFAULT_ROUTE_WEIGHTS = {
    "DEL-BOM": 0.30,
    "BLR-DEL": 0.25,
    "BLR-BOM": 0.20,
    "DEL-HYD": 0.15,
    "BOM-HYD": 0.10
}


# ============================================================
# VALIDATE WEIGHTS
# ============================================================

def validate_weights(
    route_weights: Dict[str, float]
) -> Dict[str, float]:

    if not route_weights:

        raise ValueError(
            "Route weights cannot be empty."
        )

    cleaned = {}

    for route, weight in route_weights.items():

        weight = float(weight)

        if weight < 0:

            raise ValueError(
                f"Negative weight for route: {route}"
            )

        cleaned[
            route.upper().strip()
        ] = weight

    total = sum(
        cleaned.values()
    )

    if total <= 0:

        raise ValueError(
            "Total route weight must be > 0."
        )

    # Normalize automatically.
    normalized = {

        route:
            weight / total

        for route, weight
        in cleaned.items()
    }

    logger.info(
        "Route weights normalized. Total = %.4f",
        sum(normalized.values())
    )

    return normalized


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_api_data(
    df: pd.DataFrame
) -> pd.DataFrame:

    required = {

        "route",
        "outbound_date",
        "total_fare"
    }

    missing = (
        required
        - set(df.columns)
    )

    if missing:

        raise ValueError(
            "Missing required columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    data = df.copy()

    data["route"] = (
        data["route"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    data["outbound_date"] = (
        pd.to_datetime(
            data["outbound_date"],
            errors="coerce"
        )
    )

    data["total_fare"] = (
        pd.to_numeric(
            data["total_fare"],
            errors="coerce"
        )
    )

    data = data.dropna(
        subset=[
            "route",
            "outbound_date",
            "total_fare"
        ]
    )

    data = data[
        data["total_fare"] > 0
    ]

    return data


# ============================================================
# CREATE BASE PERIOD
# ============================================================

def choose_base_period(
    df: pd.DataFrame
) -> pd.Timestamp:

    if df.empty:

        raise ValueError(
            "Cannot determine base period from empty data."
        )

    return (
        df["outbound_date"]
        .min()
    )


# ============================================================
# ROUTE BASE FARES
# ============================================================

def calculate_base_fares(
    df: pd.DataFrame,
    base_period: pd.Timestamp
) -> pd.DataFrame:

    base_data = df[
        df["outbound_date"]
        == base_period
    ]

    if base_data.empty:

        raise ValueError(
            "No observations found for base period: "
            f"{base_period.date()}"
        )

    base_fares = (
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

    return base_fares


# ============================================================
# DAILY ROUTE INDEX
# ============================================================

def calculate_daily_route_index(
    df: pd.DataFrame,
    base_period: pd.Timestamp,
    route_weights: Dict[str, float]
) -> pd.DataFrame:

    data = prepare_api_data(
        df
    )

    route_weights = validate_weights(
        route_weights
    )

    base_fares = calculate_base_fares(
        data,
        base_period
    )

    daily = (
        data.groupby(
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
            observation_count=(
                "total_fare",
                "count"
            )
        )
    )

    daily = daily.merge(
        base_fares,
        on="route",
        how="left"
    )

    daily["route_index"] = (

        daily["average_fare"]
        /
        daily["base_fare"]
        * 100
    )

    daily["route_weight"] = (
        daily["route"]
        .map(route_weights)
        .fillna(0)
    )

    daily["weighted_contribution"] = (

        daily["route_index"]
        *
        daily["route_weight"]
    )

    return daily.sort_values(
        [
            "outbound_date",
            "route"
        ]
    )


# ============================================================
# OVERALL DAILY APIx
# ============================================================

def calculate_daily_api_x(
    daily_route_data: pd.DataFrame
) -> pd.DataFrame:

    if daily_route_data.empty:

        return pd.DataFrame()

    result = (
        daily_route_data.groupby(
            "outbound_date",
            as_index=False
        )
        .agg(
            api_x=(
                "weighted_contribution",
                "sum"
            ),
            total_route_weight=(
                "route_weight",
                "sum"
            ),
            average_fare=(
                "average_fare",
                "mean"
            ),
            route_count=(
                "route",
                "nunique"
            ),
            total_observations=(
                "observation_count",
                "sum"
            )
        )
    )

    # If only a subset of routes exists on a day,
    # normalize the available weights.
    result["api_x"] = np.where(

        result["total_route_weight"] > 0,

        result["api_x"]
        /
        result["total_route_weight"],

        np.nan
    )

    result["api_x"] = (
        result["api_x"]
        .round(2)
    )

    return result.sort_values(
        "outbound_date"
    )


# ============================================================
# WEEKLY APIx
# ============================================================

def calculate_weekly_api_x(
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
            average_fare=(
                "average_fare",
                "mean"
            ),
            route_count=(
                "route_count",
                "mean"
            ),
            observations=(
                "total_observations",
                "sum"
            )
        )
    )

    weekly["api_x"] = (
        weekly["api_x"]
        .round(2)
    )

    return weekly.sort_values(
        "week_start"
    )


# ============================================================
# MONTHLY APIx
# ============================================================

def calculate_monthly_api_x(
    daily_api_x: pd.DataFrame
) -> pd.DataFrame:

    if daily_api_x.empty:

        return pd.DataFrame()

    data = daily_api_x.copy()

    data["month"] = (
        data[
            "outbound_date"
        ]
        .dt.to_period("M")
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
            average_fare=(
                "average_fare",
                "mean"
            ),
            route_count=(
                "route_count",
                "mean"
            ),
            observations=(
                "total_observations",
                "sum"
            )
        )
    )

    monthly["api_x"] = (
        monthly["api_x"]
        .round(2)
    )

    return monthly


# ============================================================
# APIx CHANGE
# ============================================================

def add_index_changes(
    df: pd.DataFrame,
    index_column: str = "api_x"
) -> pd.DataFrame:

    if df.empty:

        return df

    result = df.copy()

    result["index_change"] = (
        result[index_column]
        .diff()
    )

    result["index_change_pct"] = (
        result[index_column]
        .pct_change()
        * 100
    )

    return result


# ============================================================
# BACKTEST DATA PREPARATION
# ============================================================

def calculate_backtest_series(
    df: pd.DataFrame,
    route_weights: Dict[str, float]
) -> pd.DataFrame:

    data = prepare_api_data(
        df
    )

    if data.empty:

        return pd.DataFrame()

    dates = sorted(
        data[
            "outbound_date"
        ].dropna().unique()
    )

    if len(dates) < 2:

        logger.warning(
            "Not enough historical dates for backtesting."
        )

        return pd.DataFrame()

    route_weights = validate_weights(
        route_weights
    )

    # --------------------------------------------------------
    # BASE PERIOD
    # --------------------------------------------------------

    base_period = pd.Timestamp(
        dates[0]
    )

    base_fares = calculate_base_fares(
        data,
        base_period
    )

    # Keep only routes that exist in the base period.
    valid_routes = set(
        base_fares["route"]
    )

    data = data[
        data["route"]
        .isin(valid_routes)
    ]

    daily_route = calculate_daily_route_index(
        data,
        base_period,
        route_weights
    )

    daily_api_x = calculate_daily_api_x(
        daily_route
    )

    daily_api_x = add_index_changes(
        daily_api_x
    )

    return daily_api_x


# ============================================================
# BACKTEST METRICS
# ============================================================

def calculate_backtest_metrics(
    actual_api_x: pd.Series,
    benchmark_api_x: pd.Series
) -> Dict[str, float]:

    combined = pd.concat(

        [
            pd.Series(
                actual_api_x,
                name="actual"
            ),

            pd.Series(
                benchmark_api_x,
                name="benchmark"
            )
        ],

        axis=1
    ).dropna()

    if combined.empty:

        return {
            "mae": np.nan,
            "rmse": np.nan,
            "mape": np.nan,
            "correlation": np.nan,
            "directional_accuracy_pct": np.nan
        }

    actual = (
        combined[
            "actual"
        ].astype(float)
    )

    benchmark = (
        combined[
            "benchmark"
        ].astype(float)
    )

    errors = (
        actual
        -
        benchmark
    )

    mae = np.mean(
        np.abs(errors)
    )

    rmse = np.sqrt(
        np.mean(
            errors ** 2
        )
    )

    non_zero = (
        benchmark != 0
    )

    if non_zero.any():

        mape = (
            np.mean(
                np.abs(
                    errors[
                        non_zero
                    ]
                    /
                    benchmark[
                        non_zero
                    ]
                )
            )
            * 100
        )

    else:

        mape = np.nan

    if len(combined) >= 2:

        correlation = (
            actual
            .corr(benchmark)
        )

    else:

        correlation = np.nan

    if len(combined) >= 3:

        actual_direction = (
            np.sign(
                actual.diff()
            )
            .dropna()
        )

        benchmark_direction = (
            np.sign(
                benchmark.diff()
            )
            .dropna()
        )

        aligned = pd.concat(

            [
                actual_direction,
                benchmark_direction
            ],

            axis=1
        ).dropna()

        if not aligned.empty:

            directional_accuracy = (
                (
                    aligned.iloc[:, 0]
                    ==
                    aligned.iloc[:, 1]
                )
                .mean()
                * 100
            )

        else:

            directional_accuracy = np.nan

    else:

        directional_accuracy = np.nan

    return {

        "mae":
            round(float(mae), 4),

        "rmse":
            round(float(rmse), 4),

        "mape":
            round(float(mape), 4)
            if not np.isnan(mape)
            else np.nan,

        "correlation":
            round(float(correlation), 4)
            if not np.isnan(correlation)
            else np.nan,

        "directional_accuracy_pct":
            round(
                float(
                    directional_accuracy
                ),
                2
            )
            if not np.isnan(
                directional_accuracy
            )
            else np.nan
    }


# ============================================================
# FULL APIx PIPELINE
# ============================================================

def build_api_x(
    df: pd.DataFrame,
    route_weights: Dict[str, float]
) -> Dict[str, pd.DataFrame]:

    data = prepare_api_data(
        df
    )

    if data.empty:

        raise ValueError(
            "No valid airfare observations."
        )

    base_period = choose_base_period(
        data
    )

    logger.info(
        "APIx base period: %s",
        base_period.date()
    )

    daily_route = (
        calculate_daily_route_index(
            data,
            base_period,
            route_weights
        )
    )

    daily = (
        calculate_daily_api_x(
            daily_route
        )
    )

    weekly = (
        calculate_weekly_api_x(
            daily
        )
    )

    monthly = (
        calculate_monthly_api_x(
            daily
        )
    )

    return {

        "daily_route":
            daily_route,

        "daily":
            daily,

        "weekly":
            weekly,

        "monthly":
            monthly,

        "base_period":
            pd.DataFrame(
                {
                    "base_period":
                        [base_period]
                }
            )
    }