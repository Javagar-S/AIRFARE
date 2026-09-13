import os
import json
import logging
from typing import List, Dict, Any

import boto3
import pandas as pd
from dotenv import load_dotenv


load_dotenv()

AWS_REGION = os.getenv(
    "AWS_REGION",
    "us-east-1"
)

S3_BUCKET = os.getenv(
    "S3_BUCKET_NAME"
)

S3_ROOT = os.getenv(
    "S3_ROOT",
    "india-airfare-index"
)

PROCESSED_PREFIX = (
    f"{S3_ROOT}/processed/flights/"
)


logger = logging.getLogger(__name__)

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION
)


def list_s3_json_files(
    prefix: str = PROCESSED_PREFIX
) -> List[str]:
    """
    Return all JSON objects under the S3 prefix.
    """

    keys = []

    paginator = s3_client.get_paginator(
        "list_objects_v2"
    )

    pages = paginator.paginate(
        Bucket=S3_BUCKET,
        Prefix=prefix
    )

    for page in pages:

        for obj in page.get(
            "Contents",
            []
        ):

            key = obj.get("Key", "")

            if key.endswith(".json"):

                keys.append(key)

    logger.info(
        "Found %d JSON files in S3",
        len(keys)
    )

    return keys


def read_s3_json(
    key: str
) -> Dict[str, Any]:
    """
    Read one JSON object from S3.
    """

    response = s3_client.get_object(
        Bucket=S3_BUCKET,
        Key=key
    )

    body = response[
        "Body"
    ].read().decode(
        "utf-8"
    )

    return json.loads(body)


def load_processed_flights() -> pd.DataFrame:
    """
    Load all processed flight observations
    from S3 into a Pandas DataFrame.
    """

    records = []

    keys = list_s3_json_files()

    for key in keys:

        try:

            data = read_s3_json(key)

            # Current architecture stores each flight
            # as one JSON record.
            if isinstance(
                data,
                dict
            ):

                records.append(data)

            elif isinstance(
                data,
                list
            ):

                records.extend(data)

        except Exception as exc:

            logger.warning(
                "Could not read %s: %s",
                key,
                exc
            )

    if not records:

        logger.warning(
            "No flight records found in S3"
        )

        return pd.DataFrame()

    df = pd.DataFrame(
        records
    )

    logger.info(
        "Loaded %d records from S3",
        len(df)
    )

    return df