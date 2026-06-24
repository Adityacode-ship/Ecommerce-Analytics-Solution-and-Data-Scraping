import pandas as pd
import numpy as np
import os

def clean_data(df):


    df = df.drop_duplicates()


    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Convert numeric columns safely
    if "quantity" in df.columns:
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")

    if "unit_price" in df.columns:
        df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    # Convert date
    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce", dayfirst=True)

    # Validate required columns
    required_cols = ["quantity", "unit_price", "order_date", "order_id"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")


    # Remove invalid rows
    df = df.dropna(subset=["quantity", "unit_price", "order_date"])
    df = df[df["quantity"] > 0]
    df = df[df["unit_price"] > 0]

    return df
