import pandas as pd

REQUIRED_COLUMNS = [
    "company",
    "working_capital",
    "total_assets",
    "retained_earnings",
    "ebit",
    "market_value_equity",
    "total_liabilities",
    "sales",
]


def validate_dataframe(df: pd.DataFrame):
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")


def classify_z_score(z: float) -> str:
    if z > 2.99:
        return "Safe"
    elif z > 1.81:
        return "Grey"
    return "Distress"


def compute_altman_z(df: pd.DataFrame) -> pd.DataFrame:
    validate_dataframe(df)

    df = df.copy()

    # Ratios
    df["X1"] = df["working_capital"] / df["total_assets"]
    df["X2"] = df["retained_earnings"] / df["total_assets"]
    df["X3"] = df["ebit"] / df["total_assets"]
    df["X4"] = df["market_value_equity"] / df["total_liabilities"]
    df["X5"] = df["sales"] / df["total_assets"]

    # Z-score
    df["z_score"] = (
        1.2 * df["X1"]
        + 1.4 * df["X2"]
        + 3.3 * df["X3"]
        + 0.6 * df["X4"]
        + 1.0 * df["X5"]
    )

    # Classification
    df["risk_zone"] = df["z_score"].apply(classify_z_score)

    return df