import pandas as pd
import glob
import os
import re

def load_and_clean_data():
    base_folder = "csvdata"

    # Search all CSV files inside subfolders of csvdata/
    files = glob.glob(os.path.join(base_folder, "**", "*.csv"), recursive=True)

    # Raise error if no CSVs found
    if not files:
        raise FileNotFoundError("No CSV files found in 'csvdata/' or its subfolders.")

    # Concatenate all CSV files
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df.columns = df.columns.str.strip().str.lower()

    # Validate required columns
    if "lsoa name" not in df.columns or "month" not in df.columns:
        raise ValueError("Required columns 'lsoa name' or 'month' are missing from the data.")

    # Clean and transform
    df = df.drop_duplicates()
    df = df.dropna(subset=["lsoa name"])

    # Extract city name from LSOA name
    df["city"] = df["lsoa name"].apply(
        lambda x: re.match(r"([A-Za-z\s]+)", x).group(0).strip() if re.match(r"([A-Za-z\s]+)", x) else "Unknown"
    )

    # Convert 'month' to datetime and extract components
    df["month"] = df["month"].astype(str).str.strip()
    df["month_parsed"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")
    df = df[df["month_parsed"].notna()]  # Drop invalid dates
    df["year"] = df["month_parsed"].dt.year.astype(str)
    df["month_name"] = df["month_parsed"].dt.month_name()

    return df
