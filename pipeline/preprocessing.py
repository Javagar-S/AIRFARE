import pandas as pd
import numpy as np


def create_time_features(
    df: pd.DataFrame
) -> pd.DataFrame:

    if "outbound_date" in df.columns:

        df["travel_year"] = (
            df["outbound_date"]
            .dt.year
        )

        df["travel_month"] = (
            df["outbound_date"]
            .dt.month
        )

        df["travel_day"] = (
            df["outbound_date"]
            .dt.day
        )

        df["travel_week"] = (
            df["outbound_date"]
            .dt.isocalendar()
            .week
            .astype(int)
        )

        df["travel_day_of_week"] = (
            df["outbound_date"]
            .dt.dayofweek
        )

        df["is_weekend"] = (
            df["travel_day_of_week"]
            >= 5
        )

        df["month_name"] = (
            df["outbound_date"]
            .dt.month_name()
        )

    if "collection_timestamp" in df.columns:

        df["collection_date"] = (

            df["collection_timestamp"]
            .dt.date
        )

        df["collection_hour"] = (

            df[
                "collection_timestamp"
            ].dt.hour
        )

    return df


def create_booking_features(
    df: pd.DataFrame
) -> pd.DataFrame:

    if "advance_purchase_days" not in df.columns:

        return df

    df["booking_window_category"] = (
        pd.cut(

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
                9999
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
    )

    return df


def create_fare_features(
    df: pd.DataFrame
) -> pd.DataFrame:

    if "total_fare" not in df.columns:

        return df

    # Log transformation
    df["log_fare"] = np.log1p(
        df["total_fare"]
    )

    # Fare band
    df["fare_band"] = pd.cut(

        df["total_fare"],

        bins=[
            0,
            3000,
            5000,
            7500,
            10000,
            15000,
            np.inf
        ],

        labels=[
            "0-3000",
            "3001-5000",
            "5001-7500",
            "7501-10000",
            "10001-15000",
            "15000+"
        ]
    )

    return df


def create_route_features(
    df: pd.DataFrame
) -> pd.DataFrame:

    if "route" in df.columns:

        route_counts = (
            df[
                "route"
            ]
            .value_counts()
        )

        df[
            "route_observation_count"
        ] = df[
            "route"
        ].map(
            route_counts
        )

    return df


def create_competition_features(
    df: pd.DataFrame
) -> pd.DataFrame:

    if not {
        "route",
        "airline"
    }.issubset(df.columns):

        return df

    airline_counts = (
        df.groupby(
            "route"
        )[
            "airline"
        ]
        .transform(
            "nunique"
        )
    )

    df[
        "airline_competition_count"
    ] = airline_counts

    return df


def create_index_features(
    df: pd.DataFrame
) -> pd.DataFrame:

    if not {
        "route",
        "total_fare"
    }.issubset(df.columns):

        return df

    # Route-level average
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

    # Relative fare to route average
    df[
        "fare_vs_route_average_pct"
    ] = (

        (
            df["total_fare"]
            /
            df[
                "route_average_fare"
            ]
        )
        - 1
    ) * 100

    return df


def preprocess_dataset(
    df: pd.DataFrame
) -> pd.DataFrame:

    if df.empty:

        return df

    df = df.copy()

    df = create_time_features(
        df
    )

    df = create_booking_features(
        df
    )

    df = create_fare_features(
        df
    )

    df = create_route_features(
        df
    )

    df = create_competition_features(
        df
    )

    df = create_index_features(
        df
    )

    return df