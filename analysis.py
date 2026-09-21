"""
Customer Purchase Analysis
==========================

Executes a suite of SQL business-intelligence queries against a Neon
PostgreSQL database and prints a structured executive report covering
revenue, product, customer, geographic, and loyalty dimensions.

Environment:
    DATABASE_URL : PostgreSQL connection string (required)
                   Example: postgresql://user:pass@host/db?sslmode=require

Usage:
    python analysis.py
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError


# ============================================================
# CONFIGURATION
# ============================================================

SOURCE_TABLE = "customer"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
SECTION_WIDTH = 80
SUBSECTION_WIDTH = 70


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_database_url() -> str:
    """
    Load and normalize the DATABASE_URL from the environment.

    Returns
    -------
    str
        A SQLAlchemy-compatible PostgreSQL connection string.

    Raises
    ------
    EnvironmentError
        If DATABASE_URL is not set.
    """
    load_dotenv()

    url = os.getenv("DATABASE_URL")

    if not url:
        raise EnvironmentError(
            "DATABASE_URL is not set. Add it to your .env file or export "
            "it as an environment variable before running this script."
        )

    # SQLAlchemy 1.4+ requires the 'postgresql://' scheme.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # psycopg2 on Windows rejects Neon's 'channel_binding=require'.
    # 'sslmode=require' already enforces an encrypted channel.
    url = url.replace("&channel_binding=require", "")
    url = url.replace("?channel_binding=require&", "?")
    url = url.replace("?channel_binding=require", "")

    return url


def create_db_engine(database_url: str) -> Engine:
    """
    Create a SQLAlchemy engine tuned for Neon's serverless PostgreSQL.

    Parameters
    ----------
    database_url : str
        A valid PostgreSQL connection string.

    Returns
    -------
    Engine
        A configured SQLAlchemy engine.
    """
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
        connect_args={
            "sslmode": "require",
            "connect_timeout": 10,
        },
        future=True,
    )


# ============================================================
# QUERY HELPER
# ============================================================

def run_query(engine: Engine, query: str, label: str = "") -> pd.DataFrame:
    """
    Execute a SQL query and return the result as a DataFrame.

    Parameters
    ----------
    engine : Engine
        Active SQLAlchemy engine.
    query : str
        The SQL query to execute.
    label : str, optional
        Human-readable label used in log output.

    Returns
    -------
    pd.DataFrame
        Query results.
    """
    if label:
        logger.info("Running query: %s", label)

    with engine.connect() as connection:
        return pd.read_sql(text(query), connection)


# ============================================================
# QUERY DEFINITIONS
# ============================================================

QUERIES: dict[str, str] = {
    "overall": """
        SELECT
            SUM(purchase_amount) AS total_revenue,
            AVG(purchase_amount) AS average_purchase,
            MIN(purchase_amount) AS minimum_purchase,
            MAX(purchase_amount) AS maximum_purchase,
            COUNT(*) AS total_transactions,
            COUNT(DISTINCT customer_id) AS total_customers
        FROM customer;
    """,

    "category": """
        SELECT
            category,
            SUM(purchase_amount) AS total_revenue,
            AVG(purchase_amount) AS average_purchase,
            COUNT(*) AS transactions,
            ROUND(
                SUM(purchase_amount) * 100.0 /
                (SELECT SUM(purchase_amount) FROM customer),
                2
            ) AS revenue_percentage
        FROM customer
        GROUP BY category
        ORDER BY total_revenue DESC;
    """,

    "top_products": """
        SELECT
            item_purchased,
            category,
            SUM(purchase_amount) AS total_revenue,
            AVG(purchase_amount) AS average_purchase,
            COUNT(*) AS transactions
        FROM customer
        GROUP BY item_purchased, category
        ORDER BY total_revenue DESC
        LIMIT 10;
    """,

    "bottom_products": """
        SELECT
            item_purchased,
            category,
            SUM(purchase_amount) AS total_revenue,
            AVG(purchase_amount) AS average_purchase,
            COUNT(*) AS transactions
        FROM customer
        GROUP BY item_purchased, category
        ORDER BY total_revenue ASC
        LIMIT 10;
    """,

    "discount": """
        SELECT
            discount_applied,
            COUNT(*) AS transactions,
            SUM(purchase_amount) AS total_revenue,
            AVG(purchase_amount) AS average_purchase
        FROM customer
        GROUP BY discount_applied
        ORDER BY average_purchase DESC;
    """,

    "subscription": """
        SELECT
            subscription_status,
            COUNT(*) AS customers,
            SUM(purchase_amount) AS total_revenue,
            AVG(purchase_amount) AS average_purchase
        FROM customer
        GROUP BY subscription_status
        ORDER BY total_revenue DESC;
    """,

    "age_group": """
        SELECT
            age_group,
            COUNT(*) AS customers,
            SUM(purchase_amount) AS total_revenue,
            AVG(purchase_amount) AS average_purchase
        FROM customer
        GROUP BY age_group
        ORDER BY total_revenue DESC;
    """,

    "gender": """
        SELECT
            gender,
            COUNT(*) AS customers,
            SUM(purchase_amount) AS total_revenue,
            AVG(purchase_amount) AS average_purchase
        FROM customer
        GROUP BY gender
        ORDER BY total_revenue DESC;
    """,

    "frequency": """
        SELECT
            frequency_of_purchases,
            purchase_frequency_days,
            COUNT(*) AS customers,
            SUM(purchase_amount) AS total_revenue,
            AVG(purchase_amount) AS average_purchase
        FROM customer
        GROUP BY
            frequency_of_purchases,
            purchase_frequency_days
        ORDER BY total_revenue DESC;
    """,

    "loyalty": """
        SELECT
            CASE
                WHEN previous_purchases <= 10 THEN 'New Customer'
                WHEN previous_purchases <= 30 THEN 'Regular Customer'
                ELSE 'Loyal Customer'
            END AS customer_segment,
            COUNT(*) AS customers,
            SUM(purchase_amount) AS total_revenue,
            AVG(purchase_amount) AS average_purchase
        FROM customer
        GROUP BY customer_segment
        ORDER BY total_revenue DESC;
    """,

    "season": """
        SELECT
            season,
            COUNT(*) AS transactions,
            SUM(purchase_amount) AS total_revenue,
            AVG(purchase_amount) AS average_purchase
        FROM customer
        GROUP BY season
        ORDER BY total_revenue DESC;
    """,

    "location": """
        SELECT
            location,
            COUNT(*) AS customers,
            SUM(purchase_amount) AS total_revenue,
            AVG(purchase_amount) AS average_purchase
        FROM customer
        GROUP BY location
        ORDER BY total_revenue DESC
        LIMIT 10;
    """,

    "high_value_locations": """
        SELECT
            location,
            COUNT(*) AS customers,
            SUM(purchase_amount) AS total_revenue,
            AVG(purchase_amount) AS average_purchase
        FROM customer
        GROUP BY location
        HAVING COUNT(*) >= 20
        ORDER BY average_purchase DESC
        LIMIT 10;
    """,

    "shipping": """
        SELECT
            shipping_type,
            COUNT(*) AS transactions,
            SUM(purchase_amount) AS total_revenue,
            AVG(purchase_amount) AS average_purchase
        FROM customer
        GROUP BY shipping_type
        ORDER BY average_purchase DESC;
    """,

    "rating": """
        SELECT
            item_purchased,
            category,
            AVG(review_rating) AS average_rating,
            SUM(purchase_amount) AS total_revenue,
            AVG(purchase_amount) AS average_purchase,
            COUNT(*) AS transactions
        FROM customer
        GROUP BY item_purchased, category
        HAVING COUNT(*) >= 20
        ORDER BY average_rating DESC;
    """,

    "customer_segments": """
        SELECT
            age_group,
            subscription_status,
            frequency_of_purchases,
            COUNT(*) AS customers,
            SUM(purchase_amount) AS total_revenue,
            AVG(purchase_amount) AS average_purchase
        FROM customer
        GROUP BY
            age_group,
            subscription_status,
            frequency_of_purchases
        ORDER BY total_revenue DESC
        LIMIT 10;
    """,
}


# ============================================================
# PRESENTATION HELPERS
# ============================================================

def print_section(title: str, width: int = SECTION_WIDTH) -> None:
    """Print a large banner-style section header."""
    print("\n")
    print("=" * width)
    print(title)
    print("=" * width)


def print_subsection(title: str, width: int = SUBSECTION_WIDTH) -> None:
    """Print a smaller subsection header."""
    print(f"\n{title}")
    print("-" * width)


def print_block(
    index: int,
    title: str,
    dataframe: pd.DataFrame,
    head: int | None = None,
) -> None:
    """
    Print a numbered data block with a header and DataFrame.

    Parameters
    ----------
    index : int
        Section number.
    title : str
        Section title.
    dataframe : pd.DataFrame
        Data to display.
    head : int, optional
        Limit the number of rows displayed.
    """
    print_subsection(f"{index}. {title}")
    print(dataframe.head(head) if head else dataframe)


# ============================================================
# EXECUTIVE REPORT
# ============================================================

def build_executive_summary(results: dict[str, pd.DataFrame]) -> None:
    """
    Render the CEO-level executive summary using the collected results.

    Parameters
    ----------
    results : dict[str, pd.DataFrame]
        Mapping of query key to its DataFrame result.
    """
    overall = results["overall"]

    total_revenue = overall.loc[0, "total_revenue"]
    average_purchase = overall.loc[0, "average_purchase"]
    minimum_purchase = overall.loc[0, "minimum_purchase"]
    maximum_purchase = overall.loc[0, "maximum_purchase"]
    total_transactions = overall.loc[0, "total_transactions"]
    total_customers = overall.loc[0, "total_customers"]

    top_category = results["category"].iloc[0]
    top_product = results["top_products"].iloc[0]
    bottom_product = results["bottom_products"].iloc[0]
    top_age_group = results["age_group"].iloc[0]
    top_season = results["season"].iloc[0]
    top_location = results["location"].iloc[0]
    top_value_location = results["high_value_locations"].iloc[0]
    top_shipping = results["shipping"].iloc[0]
    top_customer_segment = results["customer_segments"].iloc[0]
    top_loyalty_segment = results["loyalty"].iloc[0]

    print_section("CEO EXECUTIVE SUMMARY")

    # ---- 1. Overall Performance ----
    print_subsection("1. OVERALL BUSINESS PERFORMANCE")
    print(f"""
Total Revenue Generated: ${total_revenue:,.2f}

Total Transactions: {total_transactions:,}

Total Customers: {total_customers:,}

Average Purchase Amount: ${average_purchase:.2f}

Purchase Amount Range:
Minimum: ${minimum_purchase:.2f}
Maximum: ${maximum_purchase:.2f}
""")

    # ---- 2. Product & Category ----
    print_subsection("2. PRODUCT AND CATEGORY PERFORMANCE")
    print(
        f"The highest revenue category is {top_category['category']} "
        f"with total revenue of ${top_category['total_revenue']:,.2f}."
    )
    print(
        f"This category contributes "
        f"{top_category['revenue_percentage']:.2f}% of total revenue."
    )
    print(
        f"The highest revenue product is {top_product['item_purchased']} "
        f"with revenue of ${top_product['total_revenue']:,.2f}."
    )
    print(
        f"The lowest revenue product is {bottom_product['item_purchased']} "
        f"with revenue of ${bottom_product['total_revenue']:,.2f}."
    )

    # ---- 3. Demographics ----
    print_subsection("3. CUSTOMER DEMOGRAPHICS")
    print(
        f"The highest revenue age group is {top_age_group['age_group']} "
        f"with revenue of ${top_age_group['total_revenue']:,.2f}."
    )
    print(
        "The strongest customer segment based on age, subscription and "
        "purchase frequency is:"
    )
    print(f"Age Group: {top_customer_segment['age_group']}")
    print(f"Subscription Status: {top_customer_segment['subscription_status']}")
    print(f"Purchase Frequency: {top_customer_segment['frequency_of_purchases']}")
    print(f"Segment Revenue: ${top_customer_segment['total_revenue']:,.2f}")

    # ---- 4. Seasonal & Geographic ----
    print_subsection("4. SEASONAL AND GEOGRAPHIC PERFORMANCE")
    print(
        f"The strongest sales season is {top_season['season']} "
        f"with revenue of ${top_season['total_revenue']:,.2f}."
    )
    print(
        f"The location generating the highest total revenue is "
        f"{top_location['location']} with revenue of "
        f"${top_location['total_revenue']:,.2f}."
    )
    print(
        f"The high-value location with the highest average purchase "
        f"(among locations with at least 20 customers) is "
        f"{top_value_location['location']} with an average purchase of "
        f"${top_value_location['average_purchase']:.2f}."
    )

    # ---- 5. Loyalty ----
    print_subsection("5. CUSTOMER LOYALTY")
    print(
        f"The customer segment generating the highest total revenue is "
        f"{top_loyalty_segment['customer_segment']} with revenue of "
        f"${top_loyalty_segment['total_revenue']:,.2f}."
    )

    # ---- 6. Shipping ----
    print_subsection("6. SHIPPING OPPORTUNITY")
    print(
        f"The shipping type with the highest average purchase is "
        f"{top_shipping['shipping_type']} with an average purchase of "
        f"${top_shipping['average_purchase']:.2f}."
    )

    # ---- 7. Discount ----
    print_subsection("7. DISCOUNT STRATEGY")

    discount_analysis = results["discount"]
    discount_yes = discount_analysis[discount_analysis["discount_applied"] == "Yes"]
    discount_no = discount_analysis[discount_analysis["discount_applied"] == "No"]

    if not discount_yes.empty and not discount_no.empty:
        discount_yes_avg = discount_yes.iloc[0]["average_purchase"]
        discount_no_avg = discount_no.iloc[0]["average_purchase"]

        print(f"Average purchase WITH discount: ${discount_yes_avg:.2f}")
        print(f"Average purchase WITHOUT discount: ${discount_no_avg:.2f}")

        if discount_yes_avg > discount_no_avg:
            print("""
INSIGHT:
Customers receiving discounts have a higher average purchase amount.

CEO RECOMMENDATION:
Continue targeted discounts for customer segments where discounts
increase spending.
""")
        else:
            print("""
INSIGHT:
Customers receiving discounts do not have a higher average purchase amount.

CEO RECOMMENDATION:
Avoid broad discounts. Use targeted promotions instead, especially for
inactive or low-frequency customers.
""")


def build_recommendations(results: dict[str, pd.DataFrame]) -> None:
    """
    Render the strategic recommendations section.

    Parameters
    ----------
    results : dict[str, pd.DataFrame]
        Mapping of query key to its DataFrame result.
    """
    top_category = results["category"].iloc[0]
    top_product = results["top_products"].iloc[0]
    top_customer_segment = results["customer_segments"].iloc[0]
    top_location = results["location"].iloc[0]
    top_value_location = results["high_value_locations"].iloc[0]
    top_season = results["season"].iloc[0]

    print_section("STRATEGIC RECOMMENDATIONS FOR THE CEO")

    print(f"""
RECOMMENDATION 1: INVEST IN HIGH-PERFORMING CATEGORIES

Focus additional marketing and inventory investment on
{top_category['category']}, the highest revenue category.

Potential actions:
- Increase advertising
- Improve product availability
- Introduce premium versions
- Cross-sell related products
""")

    print(f"""
RECOMMENDATION 2: PROMOTE THE BEST-SELLING PRODUCTS

Increase visibility for {top_product['item_purchased']}, which is currently
one of the strongest revenue-generating products.

Potential actions:
- Feature the product in campaigns
- Create complementary product bundles
- Use cross-selling recommendations
""")

    print(f"""
RECOMMENDATION 3: TARGET HIGH-VALUE CUSTOMERS

Prioritize the customer segment:

Age Group: {top_customer_segment['age_group']}
Subscription: {top_customer_segment['subscription_status']}
Purchase Frequency: {top_customer_segment['frequency_of_purchases']}

This segment currently generates the highest segment revenue.
Create personalized campaigns specifically for this customer group.
""")

    print("""
RECOMMENDATION 4: INCREASE CUSTOMER PURCHASE FREQUENCY

Encourage customers to purchase more frequently using:

- Personalized product recommendations
- Loyalty rewards
- Subscription benefits
- Reminder campaigns
- Limited-time offers
""")

    print("""
RECOMMENDATION 5: USE TARGETED DISCOUNTS

Do not automatically give discounts to all customers.

Use customer segmentation to target:

- Low-frequency customers
- New customers
- Customers with lower purchase amounts
- Customers who may need incentives to return
""")

    print(f"""
RECOMMENDATION 6: INVEST IN HIGH-POTENTIAL LOCATIONS

Increase marketing investment in high-performing locations.

The highest revenue location is:

{top_location['location']}

Also investigate locations with high average purchases, such as:

{top_value_location['location']}

These markets may represent opportunities for premium products and
targeted expansion.
""")

    print(f"""
RECOMMENDATION 7: PREPARE FOR STRONG SALES SEASONS

The strongest revenue season is:

{top_season['season']}

Before this season:

- Increase inventory
- Increase marketing campaigns
- Prepare product bundles
- Improve promotional planning
""")

    print("""
RECOMMENDATION 8: PROTECT CUSTOMER RETENTION

Build a loyalty strategy around high-value customers.

Potential programs:

- Loyalty points
- VIP rewards
- Exclusive offers
- Personalized recommendations
- Early access to products
""")


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_analysis() -> dict[str, pd.DataFrame]:
    """
    Execute all analytical queries and return the results.

    Returns
    -------
    dict[str, pd.DataFrame]
        Mapping of query key to result DataFrame.
    """
    database_url = get_database_url()
    engine = create_db_engine(database_url)

    results: dict[str, pd.DataFrame] = {}

    for key, query in QUERIES.items():
        results[key] = run_query(engine, query, label=key)

    return results


def main() -> int:
    """
    Entry point. Orchestrates queries, report, and recommendations.

    Returns
    -------
    int
        Exit code: 0 for success, 1 for failure.
    """
    logger.info("Starting customer purchase analysis.")

    try:
        results = run_analysis()

        print_section("DETAILED SQL BUSINESS ANALYSIS")

        print_block(1, "OVERALL SALES KPIs", results["overall"])
        print_block(2, "REVENUE BY CATEGORY", results["category"])
        print_block(3, "TOP 10 PRODUCTS", results["top_products"])
        print_block(4, "BOTTOM 10 PRODUCTS", results["bottom_products"])
        print_block(5, "DISCOUNT EFFECTIVENESS", results["discount"])
        print_block(6, "SUBSCRIPTION ANALYSIS", results["subscription"])
        print_block(7, "AGE GROUP ANALYSIS", results["age_group"])
        print_block(8, "GENDER ANALYSIS", results["gender"])
        print_block(9, "PURCHASE FREQUENCY ANALYSIS", results["frequency"])
        print_block(10, "CUSTOMER LOYALTY ANALYSIS", results["loyalty"])
        print_block(11, "SEASONAL ANALYSIS", results["season"])
        print_block(12, "TOP LOCATIONS BY REVENUE", results["location"])
        print_block(13, "HIGH-VALUE LOCATIONS", results["high_value_locations"])
        print_block(14, "SHIPPING TYPE ANALYSIS", results["shipping"])
        print_block(15, "PRODUCT RATING ANALYSIS", results["rating"], head=10)
        print_block(16, "TOP CUSTOMER SEGMENTS", results["customer_segments"])

        build_executive_summary(results)
        build_recommendations(results)

        print_section("ANALYSIS COMPLETE")
        print("""
This analysis provides descriptive insights into customer purchase behavior
and revenue patterns.

Important limitations:

- The dataset does not include product cost.
- Profit cannot be calculated.
- The dataset does not contain transaction dates.
- Revenue growth over time cannot be calculated.
- Each customer_id appears once in the current dataset.

Therefore, recommendations focus on increasing customer spending, improving
targeting, and identifying high-value customer and product opportunities.
""")

    except EnvironmentError as exc:
        logger.error("Configuration error: %s", exc)
        return 1

    except OperationalError as exc:
        logger.error(
            "Could not connect to the database. Verify DATABASE_URL, network "
            "access, and that the Neon project is active. Details: %s",
            exc,
        )
        return 1

    except SQLAlchemyError as exc:
        logger.error("Database error while executing queries: %s", exc)
        return 1

    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error: %s", exc)
        return 1

    logger.info("Analysis completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())