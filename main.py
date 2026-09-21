import pandas as pd




df = pd.read_csv('customer_shopping_behavior.csv')

df["Review Rating"] = df.groupby("Category")["Review Rating"].transform(
    lambda x: x.fillna(x.median())
)

df.columns = (
    df.columns
    .str.lower()
    .str.replace(" ", "_")
)

df.rename(columns={"purchase_amount_(usd)": "purchase_amount"}, inplace=True)

df["age_group"] = pd.cut(
    df["age"],
    bins=[17, 29, 44, 59, 70],
    labels=["Young Adult", "Adult", "Middle-aged", "Senior"]
)

frequency_days = {
    "Weekly": 7,
    "Bi-Weekly": 14,
    "Fortnightly": 14,
    "Monthly": 30,
    "Quarterly": 90,
    "Every 3 Months": 90,
    "Annually": 365
}

df["purchase_frequency_days"] = df["frequency_of_purchases"].map(
    frequency_days
)

df = df.drop("promo_code_used", axis=1)

