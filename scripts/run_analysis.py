import os
import sys
import logging
from pathlib import Path

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
# IMPORTS
# ============================================================

import pandas as pd

from pipeline.aggregation import (
    run_all_aggregations
)


# ============================================================
# CONFIG
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
# SAVE HELPER
# ============================================================

def save_dataframe(
    df: pd.DataFrame,
    name: str
):

    if df.empty:

        logger.warning(
            "%s is empty",
            name
        )

        return

    csv_path = (
        OUTPUT_DIR
        / f"{name}.csv"
    )

    parquet_path = (
        OUTPUT_DIR
        / f"{name}.parquet"
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
        "%s -> %d rows",
        name,
        len(df)
    )

    logger.info(
        "CSV: %s",
        csv_path
    )


# ============================================================
# MAIN
# ============================================================

def main():

    logger.info(
        "=" * 75
    )

    logger.info(
        "AIRFARE EDA AND AGGREGATION"
    )

    logger.info(
        "=" * 75
    )

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    logger.info(
        "Loading: %s",
        INPUT_FILE
    )

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input file not found: "
            f"{INPUT_FILE}"
        )

    df = pd.read_parquet(
        INPUT_FILE
    )

    logger.info(
        "Rows loaded: %d",
        len(df)
    )

    # --------------------------------------------------------
    # ANALYSIS
    # --------------------------------------------------------

    results = (
        run_all_aggregations(
            df
        )
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    save_dataframe(
        results["daily"],
        "daily_fare"
    )

    save_dataframe(
        results["weekly"],
        "weekly_fare"
    )

    save_dataframe(
        results["monthly"],
        "monthly_fare"
    )

    save_dataframe(
        results["route"],
        "route_analysis"
    )

    save_dataframe(
        results["airline"],
        "airline_analysis"
    )

    save_dataframe(
        results["booking_window"],
        "booking_window_analysis"
    )

    save_dataframe(
        results["weekday_weekend"],
        "weekday_weekend_analysis"
    )

    save_dataframe(
        results["api_x"],
        "api_x_input"
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    for name, result in results.items():

        print("\n")
        print("=" * 75)
        print(name.upper())
        print("=" * 75)

        if result.empty:

            print(
                "No data available."
            )

        else:

            print(
                result.head(10)
                .to_string(
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
        "EDA AND AGGREGATION COMPLETED"
    )

    logger.info(
        "=" * 75
    )


if __name__ == "__main__":

    main()