import sys
from pathlib import Path
import logging

import pandas as pd


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(PROJECT_ROOT)
    )


# ============================================================
# IMPORT
# ============================================================

from pipeline.api_index import (
    DEFAULT_ROUTE_WEIGHTS,
    build_api_x,
    calculate_backtest_series
)


# ============================================================
# FILES
# ============================================================

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "airfare_preprocessed.parquet"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "analytics"
    / "api_x"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
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

logger = logging.getLogger(
    __name__
)


# ============================================================
# MAIN
# ============================================================

def main():

    logger.info(
        "=" * 75
    )

    logger.info(
        "APIx CALCULATION ENGINE"
    )

    logger.info(
        "=" * 75
    )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Dataset not found: "
            f"{INPUT_FILE}"
        )

    df = pd.read_parquet(
        INPUT_FILE
    )

    logger.info(
        "Loaded records: %d",
        len(df)
    )

    # --------------------------------------------------------
    # Show configured weights
    # --------------------------------------------------------

    logger.info(
        "Route weights:"
    )

    for route, weight in (
        DEFAULT_ROUTE_WEIGHTS
        .items()
    ):

        logger.info(
            "%s = %.2f%%",
            route,
            weight * 100
        )

    # --------------------------------------------------------
    # Calculate APIx
    # --------------------------------------------------------

    results = build_api_x(

        df,

        DEFAULT_ROUTE_WEIGHTS
    )

    # --------------------------------------------------------
    # Save daily route
    # --------------------------------------------------------

    daily_route = results[
        "daily_route"
    ]

    daily_route.to_csv(

        OUTPUT_DIR
        / "daily_route_api_x.csv",

        index=False
    )

    daily_route.to_parquet(

        OUTPUT_DIR
        / "daily_route_api_x.parquet",

        index=False
    )

    # --------------------------------------------------------
    # Save daily APIx
    # --------------------------------------------------------

    daily = results[
        "daily"
    ]

    daily.to_csv(

        OUTPUT_DIR
        / "daily_api_x.csv",

        index=False
    )

    daily.to_parquet(

        OUTPUT_DIR
        / "daily_api_x.parquet",

        index=False
    )

    # --------------------------------------------------------
    # Save weekly
    # --------------------------------------------------------

    weekly = results[
        "weekly"
    ]

    weekly.to_csv(

        OUTPUT_DIR
        / "weekly_api_x.csv",

        index=False
    )

    weekly.to_parquet(

        OUTPUT_DIR
        / "weekly_api_x.parquet",

        index=False
    )

    # --------------------------------------------------------
    # Save monthly
    # --------------------------------------------------------

    monthly = results[
        "monthly"
    ]

    monthly.to_csv(

        OUTPUT_DIR
        / "monthly_api_x.csv",

        index=False
    )

    monthly.to_parquet(

        OUTPUT_DIR
        / "monthly_api_x.parquet",

        index=False
    )

    # --------------------------------------------------------
    # BACKTEST
    # --------------------------------------------------------

    logger.info(
        ""
    )

    logger.info(
        "Running historical backtest..."
    )

    backtest = calculate_backtest_series(

        df,

        DEFAULT_ROUTE_WEIGHTS
    )

    if backtest.empty:

        logger.warning(
            "Backtesting requires at least "
            "two different historical dates."
        )

    else:

        backtest.to_csv(

            OUTPUT_DIR
            / "backtest_series.csv",

            index=False
        )

        backtest.to_parquet(

            OUTPUT_DIR
            / "backtest_series.parquet",

            index=False
        )

        logger.info(
            "Backtest observations: %d",
            len(backtest)
        )

    # --------------------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------------------

    print()
    print("=" * 75)
    print("DAILY APIx")
    print("=" * 75)

    print(
        daily.to_string(
            index=False
        )
    )

    print()
    print("=" * 75)
    print("WEEKLY APIx")
    print("=" * 75)

    print(
        weekly.to_string(
            index=False
        )
    )

    print()
    print("=" * 75)
    print("MONTHLY APIx")
    print("=" * 75)

    print(
        monthly.to_string(
            index=False
        )
    )

    logger.info(
        ""
    )

    logger.info(
        "=" * 75
    )

    logger.info(
        "APIx CALCULATION COMPLETED"
    )

    logger.info(
        "=" * 75
    )


if __name__ == "__main__":

    main()