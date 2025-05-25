import pandas as pd
import glob
import re

def load_and_clean_data():
    base_folder = r"C:/Users/Mick/Desktop/Master degree UEA/SEM2/Crime data"
    files = glob.glob(base_folder + "/**/*.csv", recursive=True)
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df.columns = df.columns.str.strip().str.lower()

    # Check if required columns exist
    if "lsoa name" not in df.columns or "month" not in df.columns:
        raise ValueError("Required columns 'lsoa name' or 'month' are missing from the data.")

    df = df.drop_duplicates()  # Remove any duplicate rows
    df = df.dropna(subset=["lsoa name"])  # Ensure the LSOA code column is present

    # Create a new 'city' column by extracting the city name before the first number
    df["city"] = df["lsoa name"].apply(lambda x: re.match(r"([A-Za-z\s]+)", x).group(0).strip() if re.match(r"([A-Za-z\s]+)", x) else "Unknown")

    # Create month and year variables
    if "month" in df.columns:
        df["month"] = df["month"].astype(str).str.strip()
        df["month_parsed"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")

        # Handle any invalid 'month' values (drop or replace them)
        df = df[df["month_parsed"].notna()]
        df["year"] = df["month_parsed"].dt.year.astype(str)
        df["month_name"] = df["month_parsed"].dt.month_name()

    return df
