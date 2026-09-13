import os
import logging
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from flask import (
    Flask,
    jsonify,
    render_template,
    request
)

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

PROCESSED_DIR = DATA_DIR / "processed"

ANALYTICS_DIR = DATA_DIR / "analytics"

API_X_DIR = ANALYTICS_DIR / "api_x"

PROCESSED_FILE = (
    PROCESSED_DIR
    / "airfare_preprocessed.parquet"
)


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

app.config["JSON_SORT_KEYS"] = False


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

logger = logging.getLogger(
    "airfare_app"
)


# ============================================================
# CACHE
# ============================================================

DATA_CACHE = {

    "data": None,

    "mtime": None
}


CACHE_SECONDS = int(
    os.getenv(
        "CACHE_SECONDS",
        "30"
    )
)

LAST_CACHE_CHECK = 0


# ============================================================
# GLOBAL NO-CACHE FOR DEVELOPMENT
# ============================================================

@app.after_request
def disable_browser_cache(response):

    response.headers[
        "Cache-Control"
    ] = (
        "no-store, "
        "no-cache, "
        "must-revalidate, "
        "max-age=0"
    )

    response.headers[
        "Pragma"
    ] = "no-cache"

    response.headers[
        "Expires"
    ] = "0"

    return response


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def now_utc():
    return datetime.now(
        timezone.utc
    )


def safe_value(value):

    if value is None:
        return None

    try:

        if pd.isna(value):
            return None

    except Exception:
        pass

    if isinstance(
        value,
        np.integer
    ):
        return int(value)

    if isinstance(
        value,
        np.floating
    ):
        return float(value)

    if isinstance(
        value,
        np.bool_
    ):
        return bool(value)

    if isinstance(
        value,
        (
            pd.Timestamp,
            datetime
        )
    ):
        return value.isoformat()

    return value


def records_from_dataframe(
    dataframe
):

    if (
        dataframe is None
        or dataframe.empty
    ):
        return []

    result = []

    for row in dataframe.to_dict(
        orient="records"
    ):

        clean_row = {}

        for key, value in row.items():

            clean_row[key] = safe_value(
                value
            )

        result.append(
            clean_row
        )

    return result


def success_response(
    data,
    **metadata
):

    payload = {

        "success": True,

        "generated_at":
            now_utc().isoformat(),

        "data":
            data
    }

    payload.update(
        metadata
    )

    return jsonify(
        payload
    )


def error_response(
    message,
    status=500
):

    return jsonify({

        "success": False,

        "generated_at":
            now_utc().isoformat(),

        "error":
            str(message)

    }), status


# ============================================================
# DATA NORMALIZATION
# ============================================================

def normalize_dataset(
    dataframe
):

    df = dataframe.copy()

    # --------------------------------------------------------
    # Date columns
    # --------------------------------------------------------

    date_columns = [

        "collection_timestamp",

        "collection_date",

        "outbound_date",

        "return_date",

        "search_timestamp",

        "searched_at"
    ]

    for column in date_columns:

        if column in df.columns:

            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )


    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    numeric_columns = [

        "total_fare",

        "price",

        "base_fare",

        "taxes_fees",

        "advance_purchase_days",

        "stops",

        "total_duration_minutes",

        "duration_minutes",

        "carbon_emissions_kg",

        "seats_available",

        "route_average_fare",

        "fare_vs_route_average_pct",

        "route_airline_count",

        "route_observation_count"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )


    # --------------------------------------------------------
    # Fare
    # --------------------------------------------------------

    if (
        "total_fare"
        not in df.columns
    ):

        if "price" in df.columns:

            df["total_fare"] = (
                df["price"]
            )


    # --------------------------------------------------------
    # Route
    # --------------------------------------------------------

    if (
        "route" not in df.columns
    ):

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

                + df[
                    "destination"
                ]
                .astype(str)
                .str.upper()
                .str.strip()

            )


    # --------------------------------------------------------
    # Airline
    # --------------------------------------------------------

    if "airline" in df.columns:

        df["airline"] = (
            df["airline"]
            .astype("string")
            .str.strip()
        )


    # --------------------------------------------------------
    # Fare quality
    # --------------------------------------------------------

    if "total_fare" in df.columns:

        df = df[
            df["total_fare"] > 0
        ]


    return df.reset_index(
        drop=True
    )


# ============================================================
# LOAD PROCESSED DATA
# ============================================================

def load_data():

    global LAST_CACHE_CHECK

    if not PROCESSED_FILE.exists():

        logger.error(
            "Processed dataset not found: %s",
            PROCESSED_FILE
        )

        return pd.DataFrame()


    try:

        current_mtime = (
            PROCESSED_FILE
            .stat()
            .st_mtime
        )

    except OSError:

        return pd.DataFrame()


    current_time = (
        datetime.now().timestamp()
    )


    # --------------------------------------------------------
    # Cache
    # --------------------------------------------------------

    if (

        DATA_CACHE["data"]
        is not None

        and

        DATA_CACHE["mtime"]
        == current_mtime

        and

        current_time
        -
        LAST_CACHE_CHECK
        < CACHE_SECONDS

    ):

        return DATA_CACHE[
            "data"
        ].copy()


    # --------------------------------------------------------
    # Reload
    # --------------------------------------------------------

    try:

        logger.info(
            "Loading dataset: %s",
            PROCESSED_FILE
        )

        dataframe = pd.read_parquet(
            PROCESSED_FILE
        )

        dataframe = normalize_dataset(
            dataframe
        )

        DATA_CACHE[
            "data"
        ] = dataframe.copy()

        DATA_CACHE[
            "mtime"
        ] = current_mtime

        LAST_CACHE_CHECK = current_time

        logger.info(
            "Loaded airfare_preprocessed.parquet (%d rows)",
            len(dataframe)
        )

        return dataframe.copy()

    except Exception as exc:

        logger.exception(
            "Unable to load processed dataset"
        )

        return pd.DataFrame()


# ============================================================
# LOAD OPTIONAL ANALYTICS
# ============================================================

def load_optional_analytics(
    filename,
    api_x=False
):

    directory = (
        API_X_DIR
        if api_x
        else ANALYTICS_DIR
    )

    path = (
        directory
        / filename
    )

    if not path.exists():

        return pd.DataFrame()


    try:

        dataframe = pd.read_parquet(
            path
        )

        return normalize_dataset(
            dataframe
        )

    except Exception as exc:

        logger.warning(
            "Optional analytics file unavailable: %s | %s",
            path,
            exc
        )

        return pd.DataFrame()


# ============================================================
# PAGE ROUTE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "dashboard.html"
    )


@app.route("/dashboard")
def dashboard():

    return render_template(
        "dashboard.html"
    )


# Keep these routes available if you
# still have the older templates.

@app.route("/intelligence")
def intelligence():

    return render_template(
        "dashboard.html"
    )


@app.route("/methodology")
def methodology():

    return render_template(
        "methodology.html",
        active_page="methodology"
    )


# ============================================================
# HEALTH
# ============================================================

@app.route("/api/health")
def health():

    df = load_data()

    return success_response({

        "status":
            "healthy"
            if not df.empty
            else "no-data",

        "dataset_available":
            not df.empty,

        "records":
            int(len(df)),

        "dataset":
            str(PROCESSED_FILE)
    })


# ============================================================
# SUMMARY
# ============================================================

@app.route("/api/summary")
def summary():

    try:

        df = load_data()

        if df.empty:

            return success_response({

                "api_x": 100.0,

                "api_x_change": 0.0,

                "average_fare": 0.0,

                "minimum_fare": 0.0,

                "maximum_fare": 0.0,

                "routes": 0,

                "airlines": 0,

                "observations": 0,

                "travel_dates": 0,

                "updated_at": None

            })


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

        routes = int(
            df[
                "route"
            ].nunique()
        )

        airlines = int(
            df[
                "airline"
            ].nunique()
        )

        observations = int(
            len(df)
        )

        travel_dates = int(
            df[
                "outbound_date"
            ].nunique()
        )


        # ----------------------------------------------------
        # APIx
        # ----------------------------------------------------

        api_x_df = load_optional_analytics(
            "daily_api_x.parquet",
            api_x=True
        )


        if (
            not api_x_df.empty
            and
            "api_x"
            in api_x_df.columns
        ):

            api_x_df[
                "outbound_date"
            ] = pd.to_datetime(
                api_x_df[
                    "outbound_date"
                ],
                errors="coerce"
            )

            api_x_df = (
                api_x_df
                .dropna(
                    subset=[
                        "outbound_date",
                        "api_x"
                    ]
                )
                .sort_values(
                    "outbound_date"
                )
            )


        if not api_x_df.empty:

            api_x = float(
                api_x_df.iloc[-1][
                    "api_x"
                ]
            )

            if len(api_x_df) >= 2:

                previous = float(
                    api_x_df.iloc[-2][
                        "api_x"
                    ]
                )

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

                ) if previous != 0 else 0

            else:

                api_x_change = 0

        else:

            daily = (
                df.groupby(
                    "outbound_date"
                )[
                    "total_fare"
                ]
                .mean()
                .sort_index()
            )

            if daily.empty:

                api_x = 100.0

                api_x_change = 0.0

            else:

                base = float(
                    daily.iloc[0]
                )

                if base > 0:

                    api_x = (

                        float(
                            daily.iloc[-1]
                        )
                        /
                        base
                        *
                        100

                    )

                else:

                    api_x = 100.0

                if len(daily) >= 2:

                    previous = float(
                        daily.iloc[-2]
                    )

                    if previous > 0:

                        api_x_change = (

                            (
                                float(
                                    daily.iloc[-1]
                                )
                                -
                                previous
                            )
                            /
                            previous
                            *
                            100

                        )

                    else:

                        api_x_change = 0

                else:

                    api_x_change = 0


        # ----------------------------------------------------
        # Latest collection
        # ----------------------------------------------------

        updated_at = None

        if (
            "collection_timestamp"
            in df.columns
        ):

            latest = (
                df[
                    "collection_timestamp"
                ].max()
            )

            if pd.notna(latest):

                updated_at = (
                    latest.isoformat()
                )


        return success_response({

            "api_x":
                round(
                    api_x,
                    2
                ),

            "api_x_change":
                round(
                    api_x_change,
                    2
                ),

            "average_fare":
                round(
                    average_fare,
                    2
                ),

            "minimum_fare":
                round(
                    minimum_fare,
                    2
                ),

            "maximum_fare":
                round(
                    maximum_fare,
                    2
                ),

            "routes":
                routes,

            "airlines":
                airlines,

            "observations":
                observations,

            "travel_dates":
                travel_dates,

            "updated_at":
                updated_at

        })

    except Exception as exc:

        logger.exception(
            "Summary API failed"
        )

        return error_response(
            exc
        )


# ============================================================
# COMPLETE SINGLE-PAGE DASHBOARD API
# ============================================================

@app.route("/api/dashboard")
def dashboard_api():

    try:

        df = load_data()


        if df.empty:

            return success_response({

                "summary": {},

                "trend": [],

                "routes": [],

                "airlines": [],

                "booking_window": [],

                "distribution": [],

                "quality": {},

                "recent_flights": []

            })


        # ====================================================
        # SUMMARY
        # ====================================================

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

        route_count = int(
            df[
                "route"
            ].nunique()
        )

        airline_count = int(
            df[
                "airline"
            ].nunique()
        )

        observation_count = int(
            len(df)
        )

        travel_date_count = int(
            df[
                "outbound_date"
            ].nunique()
        )


        # ====================================================
        # APIx
        # ====================================================

        api_x_file = (
            load_optional_analytics(
                "daily_api_x.parquet",
                api_x=True
            )
        )


        trend = []

        api_x_current = 100.0

        api_x_change = 0.0


        if (

            not api_x_file.empty

            and

            "api_x"
            in api_x_file.columns

        ):

            api_x_file[
                "outbound_date"
            ] = pd.to_datetime(
                api_x_file[
                    "outbound_date"
                ],
                errors="coerce"
            )

            api_x_file = (
                api_x_file
                .dropna(
                    subset=[
                        "outbound_date",
                        "api_x"
                    ]
                )
                .sort_values(
                    "outbound_date"
                )
            )


            for _, row in (
                api_x_file.iterrows()
            ):

                trend.append({

                    "date":
                        row[
                            "outbound_date"
                        ].strftime(
                            "%Y-%m-%d"
                        ),

                    "api_x":
                        float(
                            row["api_x"]
                        )

                })


            if trend:

                api_x_current = (
                    trend[-1]["api_x"]
                )


            if len(trend) >= 2:

                previous = (
                    trend[-2]["api_x"]
                )

                if previous != 0:

                    api_x_change = (

                        (
                            api_x_current
                            -
                            previous
                        )
                        /
                        previous
                        *
                        100

                    )


        else:

            # ------------------------------------------------
            # Direct fallback
            # ------------------------------------------------

            daily_fare = (
                df.groupby(
                    "outbound_date"
                )[
                    "total_fare"
                ]
                .mean()
                .sort_index()
            )


            if not daily_fare.empty:

                base_fare = float(
                    daily_fare.iloc[0]
                )

                if base_fare > 0:

                    for (
                        date_value,
                        fare
                    ) in daily_fare.items():

                        trend.append({

                            "date":
                                date_value.strftime(
                                    "%Y-%m-%d"
                                ),

                            "api_x":
                                round(
                                    float(fare)
                                    /
                                    base_fare
                                    *
                                    100,
                                    2
                                )

                        })


                if trend:

                    api_x_current = (
                        trend[-1][
                            "api_x"
                        ]
                    )


                if len(trend) >= 2:

                    previous = (
                        trend[-2][
                            "api_x"
                        ]
                    )

                    if previous != 0:

                        api_x_change = (

                            (
                                api_x_current
                                -
                                previous
                            )
                            /
                            previous
                            *
                            100

                        )


        # ====================================================
        # ROUTE ANALYSIS
        # ====================================================

        route_df = (
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


        route_std = (
            df.groupby(
                "route"
            )[
                "total_fare"
            ]
            .std()
            .fillna(0)
            .rename(
                "fare_std"
            )
        )


        route_df = route_df.merge(
            route_std,
            on="route",
            how="left"
        )


        route_df[
            "volatility_pct"
        ] = (

            route_df[
                "fare_std"
            ]
            /
            route_df[
                "average_fare"
            ]
            *
            100

        ).replace(
            [np.inf, -np.inf],
            np.nan
        ).fillna(0)


        route_df[
            "fare_range"
        ] = (

            route_df[
                "maximum_fare"
            ]
            -
            route_df[
                "minimum_fare"
            ]

        )


        route_df = route_df.sort_values(
            "average_fare",
            ascending=False
        )


        # ====================================================
        # AIRLINE ANALYSIS
        # ====================================================

        airline_df = (
            df.groupby(
                "airline",
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

                routes=(
                    "route",
                    "nunique"
                )

            )
        )


        airline_df = airline_df.sort_values(
            "average_fare",
            ascending=False
        )


        # ====================================================
        # BOOKING WINDOW
        # ====================================================

        booking_df = pd.DataFrame()


        if (
            "advance_purchase_days"
            in df.columns
        ):

            booking_data = df.copy()


            booking_data[
                "advance_purchase_days"
            ] = pd.to_numeric(
                booking_data[
                    "advance_purchase_days"
                ],
                errors="coerce"
            )


            booking_data = (
                booking_data
                .dropna(
                    subset=[
                        "advance_purchase_days"
                    ]
                )
            )


            booking_data[
                "booking_window"
            ] = pd.cut(

                booking_data[
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


            booking_df = (
                booking_data
                .groupby(
                    "booking_window",
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


        # ====================================================
        # FARE DISTRIBUTION
        # ====================================================

        distribution_data = df.copy()


        distribution_data[
            "fare_bucket"
        ] = pd.cut(

            distribution_data[
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
                "<= ₹5K",
                "₹5K–7.5K",
                "₹7.5K–10K",
                "₹10K–15K",
                "₹15K–25K",
                "₹25K–50K",
                "₹50K+"
            ]

        )


        distribution_df = (
            distribution_data
            .groupby(
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


        # ====================================================
        # DATA QUALITY
        # ====================================================

        duplicate_count = 0


        if "record_id" in df.columns:

            duplicate_count = int(
                df[
                    "record_id"
                ]
                .duplicated()
                .sum()
            )


        missing_fare = int(
            df[
                "total_fare"
            ]
            .isna()
            .sum()
        )


        missing_airline = int(
            df[
                "airline"
            ]
            .isna()
            .sum()
        )


        outlier_count = 0


        if (
            "fare_outlier"
            in df.columns
        ):

            outlier_count = int(
                df[
                    "fare_outlier"
                ]
                .fillna(False)
                .sum()
            )


        total_cells = (
            len(df)
            *
            len(df.columns)
        )


        missing_cells = int(
            df
            .isna()
            .sum()
            .sum()
        )


        completeness = (

            (
                1
                -
                (
                    missing_cells
                    /
                    total_cells
                )
            )
            *
            100

            if total_cells > 0

            else 0
        )


        # ====================================================
        # RECENT FLIGHTS
        # ====================================================

        recent = df.copy()


        if (
            "collection_timestamp"
            in recent.columns
        ):

            recent = recent.sort_values(
                "collection_timestamp",
                ascending=False
            )


        recent = recent.head(
            15
        )


        # ====================================================
        # PAYLOAD
        # ====================================================

        payload = {

            "summary": {

                "api_x":
                    round(
                        api_x_current,
                        2
                    ),

                "api_x_change":
                    round(
                        api_x_change,
                        2
                    ),

                "average_fare":
                    round(
                        average_fare,
                        2
                    ),

                "minimum_fare":
                    round(
                        minimum_fare,
                        2
                    ),

                "maximum_fare":
                    round(
                        maximum_fare,
                        2
                    ),

                "routes":
                    route_count,

                "airlines":
                    airline_count,

                "observations":
                    observation_count,

                "travel_dates":
                    travel_date_count

            },


            "trend":
                trend,


            "routes":
                records_from_dataframe(
                    route_df.head(
                        25
                    )
                ),


            "airlines":
                records_from_dataframe(
                    airline_df
                ),


            "booking_window":
                records_from_dataframe(
                    booking_df
                ),


            "distribution":
                records_from_dataframe(
                    distribution_df
                ),


            "quality": {

                "records":
                    observation_count,

                "duplicates":
                    duplicate_count,

                "missing_fare":
                    missing_fare,

                "missing_airline":
                    missing_airline,

                "outliers":
                    outlier_count,

                "routes":
                    route_count,

                "airlines":
                    airline_count,

                "completeness_pct":
                    round(
                        completeness,
                        2
                    )

            },


            "recent_flights":
                records_from_dataframe(
                    recent
                )

        }


        logger.info(
            "Dashboard payload generated: %d observations",
            observation_count
        )


        return success_response(
            payload
        )


    except Exception as exc:

        logger.exception(
            "Dashboard API failed"
        )

        return error_response(
            exc
        )


# ============================================================
# FILTERS
# ============================================================

@app.route("/api/filters")
def filters():

    try:

        df = load_data()

        if df.empty:

            return success_response({

                "routes": [],

                "airlines": [],

                "travel_dates": []

            })


        routes = sorted(
            df[
                "route"
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )


        airlines = sorted(
            df[
                "airline"
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )


        travel_dates = sorted(

            pd.to_datetime(
                df[
                    "outbound_date"
                ],
                errors="coerce"
            )
            .dropna()
            .dt
            .strftime(
                "%Y-%m-%d"
            )
            .unique()
            .tolist()

        )


        return success_response({

            "routes":
                routes,

            "airlines":
                airlines,

            "travel_dates":
                travel_dates

        })


    except Exception as exc:

        return error_response(
            exc
        )


# ============================================================
# ROUTE API
# ============================================================

@app.route("/api/routes")
def route_api():

    try:

        df = load_data()

        if df.empty:

            return success_response([])


        result = (
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


        result = result.sort_values(
            "average_fare",
            ascending=False
        )


        return success_response(
            records_from_dataframe(
                result
            )
        )


    except Exception as exc:

        logger.exception(
            "Route API failed"
        )

        return error_response(
            exc
        )


# ============================================================
# AIRLINE API
# ============================================================

@app.route("/api/airlines")
def airline_api():

    try:

        df = load_data()

        if df.empty:

            return success_response([])


        route = request.args.get(
            "route"
        )


        if (
            route
            and
            route.lower() != "all"
        ):

            df = df[
                df[
                    "route"
                ]
                .astype(str)
                .str.upper()
                ==
                route.upper()
            ]


        result = (
            df.groupby(
                "airline",
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

                routes=(
                    "route",
                    "nunique"
                )

            )
        )


        result = result.sort_values(
            "average_fare",
            ascending=False
        )


        return success_response(
            records_from_dataframe(
                result
            )
        )


    except Exception as exc:

        return error_response(
            exc
        )


# ============================================================
# FLIGHT OBSERVATIONS API
# ============================================================

@app.route("/api/flights")
def flight_api():

    try:

        df = load_data()

        if df.empty:

            return success_response([])


        route = request.args.get(
            "route"
        )

        airline = request.args.get(
            "airline"
        )


        if (
            route
            and
            route.lower() != "all"
        ):

            df = df[
                df[
                    "route"
                ]
                .astype(str)
                .str.upper()
                ==
                route.upper()
            ]


        if (
            airline
            and
            airline.lower() != "all"
        ):

            df = df[
                df[
                    "airline"
                ]
                .astype(str)
                .str.lower()
                ==
                airline.lower()
            ]


        if (
            "collection_timestamp"
            in df.columns
        ):

            df = df.sort_values(
                "collection_timestamp",
                ascending=False
            )


        limit = request.args.get(
            "limit",
            100,
            type=int
        )


        limit = max(
            1,
            min(
                limit,
                1000
            )
        )


        return success_response(
            records_from_dataframe(
                df.head(
                    limit
                )
            )
        )


    except Exception as exc:

        return error_response(
            exc
        )


# ============================================================
# DATA QUALITY API
# ============================================================

@app.route("/api/data-quality")
def data_quality():

    try:

        df = load_data()

        if df.empty:

            return success_response({})

        duplicates = 0

        if "record_id" in df.columns:

            duplicates = int(
                df[
                    "record_id"
                ]
                .duplicated()
                .sum()
            )


        outliers = 0

        if "fare_outlier" in df.columns:

            outliers = int(
                df[
                    "fare_outlier"
                ]
                .fillna(False)
                .sum()
            )


        missing_fare = int(
            df[
                "total_fare"
            ]
            .isna()
            .sum()
        )


        missing_airline = int(
            df[
                "airline"
            ]
            .isna()
            .sum()
        )


        cells = (
            len(df)
            *
            len(df.columns)
        )


        missing_cells = int(
            df.isna()
            .sum()
            .sum()
        )


        completeness = (

            1
            -
            missing_cells
            /
            cells

        ) * 100 if cells > 0 else 0


        return success_response({

            "records":
                len(df),

            "duplicates":
                duplicates,

            "outliers":
                outliers,

            "missing_fare":
                missing_fare,

            "missing_airline":
                missing_airline,

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
                ),

            "completeness_pct":
                round(
                    completeness,
                    2
                )

        })


    except Exception as exc:

        return error_response(
            exc
        )


# ============================================================
# STATUS
# ============================================================

@app.route("/api/status")
def status():

    df = load_data()

    return success_response({

        "application":
            "India Airfare Intelligence",

        "status":
            "operational"
            if not df.empty
            else "no-data",

        "records":
            int(len(df)),

        "processed_dataset":
            str(PROCESSED_FILE),

        "analytics_directory":
            str(ANALYTICS_DIR),

        "server_time":
            now_utc().isoformat(),

        "version":
            "1.0.0"

    })


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def handle_404(error):

    if request.path.startswith(
        "/api/"
    ):

        return error_response(
            "API endpoint not found",
            404
        )

    return render_template(
        "dashboard.html"
    ), 404


@app.errorhandler(500)
def handle_500(error):

    logger.exception(
        "Unhandled application error"
    )

    if request.path.startswith(
        "/api/"
    ):

        return error_response(
            "Internal server error",
            500
        )

    return (
        render_template(
            "dashboard.html"
        ),
        500
    )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    host = os.getenv(
        "FLASK_HOST",
        "127.0.0.1"
    )

    port = int(
        os.getenv(
            "FLASK_PORT",
            "5000"
        )
    )

    debug = (
        os.getenv(
            "FLASK_DEBUG",
            "true"
        ).lower()
        == "true"
    )


    logger.info(
        "=" * 80
    )

    logger.info(
        "INDIA AIRFARE INTELLIGENCE PLATFORM"
    )

    logger.info(
        "=" * 80
    )


    dataframe = load_data()


    if dataframe.empty:

        logger.warning(
            "No processed dataset available."
        )

    else:

        logger.info(
            "Processed records: %d",
            len(dataframe)
        )

        logger.info(
            "Routes: %d",
            dataframe[
                "route"
            ].nunique()
        )

        logger.info(
            "Airlines: %d",
            dataframe[
                "airline"
            ].nunique()
        )

        logger.info(
            "Average fare: %.2f",
            dataframe[
                "total_fare"
            ].mean()
        )

        logger.info(
            "Minimum fare: %.2f",
            dataframe[
                "total_fare"
            ].min()
        )

        logger.info(
            "Maximum fare: %.2f",
            dataframe[
                "total_fare"
            ].max()
        )


    logger.info(
        "Dashboard API: "
        "http://%s:%d/api/dashboard",
        host,
        port
    )

    logger.info(
        "Website: "
        "http://%s:%d/dashboard",
        host,
        port
    )


    app.run(

        host=host,

        port=port,

        debug=debug,

        threaded=True
    )
