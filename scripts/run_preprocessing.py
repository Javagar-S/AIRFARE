import sys
from pathlib import Path

# ============================================================
# ADD PROJECT ROOT TO PYTHON PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORTS
# ============================================================

import os
import logging

import pandas as pd
from dotenv import load_dotenv

from pipeline.s3_loader import load_processed_flights
from pipeline.cleaning import clean_dataset
from pipeline.preprocessing import preprocess_dataset
from pipeline.validation import generate_quality_report

import os
import logging

import pandas as pd
from dotenv import load_dotenv

from pipeline.s3_loader import (
    load_processed_flights
)

from pipeline.cleaning import (
    clean_dataset
)

from pipeline.preprocessing import (
    preprocess_dataset
)

from pipeline.validation import (
    generate_quality_report
)


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

os.makedirs(
    "data/cleaned",
    exist_ok=True
)

os.makedirs(
    "data/processed",
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
        "=" * 70
    )

    logger.info(
        "AIRFARE S3 DATA PREPROCESSING"
    )

    logger.info(
        "=" * 70
    )

    # --------------------------------------------------------
    # STEP 1: LOAD FROM S3
    # --------------------------------------------------------

    df = load_processed_flights()

    if df.empty:

        logger.error(
            "No records loaded from S3."
        )

        return

    logger.info(
        "Raw S3 records: %d",
        len(df)
    )

    # --------------------------------------------------------
    # STEP 2: CLEANING
    # --------------------------------------------------------

    cleaned_df = clean_dataset(
        df
    )

    logger.info(
        "Cleaned records: %d",
        len(cleaned_df)
    )

    # --------------------------------------------------------
    # STEP 3: QUALITY REPORT
    # --------------------------------------------------------

    report = (
        generate_quality_report(
            cleaned_df
        )
    )

    logger.info(
        "DATA QUALITY REPORT"
    )

    for key, value in report.items():

        logger.info(
            "%s: %s",
            key,
            value
        )

    # --------------------------------------------------------
    # STEP 4: SAVE CLEANED DATA
    # --------------------------------------------------------

    cleaned_csv = (
        "data/cleaned/"
        "airfare_cleaned.csv"
    )

    cleaned_parquet = (
        "data/cleaned/"
        "airfare_cleaned.parquet"
    )

    cleaned_df.to_csv(
        cleaned_csv,
        index=False
    )

    cleaned_df.to_parquet(
        cleaned_parquet,
        index=False
    )

    logger.info(
        "Cleaned CSV saved: %s",
        cleaned_csv
    )

    logger.info(
        "Cleaned Parquet saved: %s",
        cleaned_parquet
    )

    # --------------------------------------------------------
    # STEP 5: PREPROCESSING
    # --------------------------------------------------------

    processed_df = (
        preprocess_dataset(
            cleaned_df
        )
    )

    logger.info(
        "Preprocessed records: %d",
        len(processed_df)
    )

    # --------------------------------------------------------
    # STEP 6: SAVE PROCESSED DATA
    # --------------------------------------------------------

    processed_csv = (
        "data/processed/"
        "airfare_preprocessed.csv"
    )

    processed_parquet = (
        "data/processed/"
        "airfare_preprocessed.parquet"
    )

    processed_df.to_csv(
        processed_csv,
        index=False
    )

    processed_df.to_parquet(
        processed_parquet,
        index=False
    )

    logger.info(
        "Processed CSV saved: %s",
        processed_csv
    )

    logger.info(
        "Processed Parquet saved: %s",
        processed_parquet
    )

    # --------------------------------------------------------
    # STEP 7: SAMPLE
    # --------------------------------------------------------

    logger.info(
        ""
    )

    logger.info(
        "DATASET SAMPLE:"
    )

    print(
        processed_df.head(10).to_string()
    )

    logger.info(
        ""
    )

    logger.info(
        "=" * 70
    )

    logger.info(
        "PREPROCESSING COMPLETED"
    )

    logger.info(
        "=" * 70
    )


if __name__ == "__main__":

    main()