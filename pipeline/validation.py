import pandas as pd


def generate_quality_report(
    df: pd.DataFrame
) -> dict:

    if df.empty:

        return {
            "rows": 0,
            "columns": 0
        }

    report = {

        "rows": len(df),

        "columns": len(df.columns),

        "duplicate_record_ids": (
            df["record_id"]
            .duplicated()
            .sum()
            if "record_id"
            in df.columns
            else None
        ),

        "missing_total_fare": (
            df["total_fare"]
            .isna()
            .sum()
            if "total_fare"
            in df.columns
            else None
        ),

        "missing_airline": (
            df["airline"]
            .isna()
            .sum()
            if "airline"
            in df.columns
            else None
        ),

        "negative_fares": (
            (
                df["total_fare"]
                < 0
            ).sum()
            if "total_fare"
            in df.columns
            else None
        ),

        "unique_routes": (
            df["route"]
            .nunique()
            if "route"
            in df.columns
            else None
        ),

        "unique_airlines": (
            df["airline"]
            .nunique()
            if "airline"
            in df.columns
            else None
        )
    }

    return report