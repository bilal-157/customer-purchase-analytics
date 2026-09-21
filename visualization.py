"""
Customer Purchase Visualizations
================================

Generates six business-intelligence charts from a Neon PostgreSQL
`customer` table and saves each as a PNG file.

Charts Produced:
    revenue_by_category.png       - Revenue by category
    top_10_products.png           - Top 10 products by revenue
    revenue_by_age_group.png      - Revenue by age group
    discount_effectiveness.png    - Avg purchase: discount vs no discount
    revenue_by_season.png         - Revenue by season
    subscription_analysis.png     - Avg purchase by subscription status

Environment:
    DATABASE_URL : PostgreSQL connection string (required)
                   Example: postgresql://user:pass@host/db?sslmode=require

Usage:
    python charts.py
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Callable

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_DIR = Path(".").resolve()
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Use a non-interactive backend when running headless (CI, servers).
# Remove this line if you want interactive windows locally.
if os.getenv("CI") or os.getenv("HEADLESS"):
    matplotlib.use("Agg")


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
# CHART HELPERS
# ============================================================

def save_chart(
    filename: str,
    plot_fn: Callable[[], None],
    *,
    title: str,
) -> None:
    """
    Execute a plot function, save it to disk, and close the figure.

    Parameters
    ----------
    filename : str
        Name of the output PNG file (relative to OUTPUT_DIR).
    plot_fn : Callable[[], None]
        Function that draws onto the current matplotlib figure.
    title : str
        Human-readable chart label for logging.
    """
    logger.info("Rendering chart: %s", title)

    plt.figure()
    plot_fn()

    output_path = OUTPUT_DIR / filename

    plt.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close()

    logger.info("Saved: %s", output_path)


# ============================================================
# CHART 1: REVENUE BY CATEGORY
# ============================================================

def chart_revenue_by_category(engine: Engine) -> None:
    """Bar chart of total revenue per product category."""
    query = """
        SELECT
            category,
            SUM(purchase_amount) AS total_revenue
        FROM customer
        GROUP BY category
        ORDER BY total_revenue DESC;
    """

    df = run_query(engine, query, label="revenue_by_category")

    def draw() -> None:
        plt.figure(figsize=(10, 6))
        plt.bar(df["category"], df["total_revenue"])
        plt.title("Revenue by Category")
        plt.xlabel("Category")
        plt.ylabel("Total Revenue ($)")
        plt.xticks(rotation=45)

    save_chart("revenue_by_category.png", draw, title="Revenue by Category")


# ============================================================
# CHART 2: TOP 10 PRODUCTS
# ============================================================

def chart_top_products(engine: Engine) -> None:
    """Horizontal bar chart of the top 10 products by revenue."""
    query = """
        SELECT
            item_purchased,
            SUM(purchase_amount) AS total_revenue
        FROM customer
        GROUP BY item_purchased
        ORDER BY total_revenue DESC
        LIMIT 10;
    """

    df = run_query(engine, query, label="top_10_products")

    def draw() -> None:
        plt.figure(figsize=(10, 6))
        plt.barh(df["item_purchased"], df["total_revenue"])
        plt.title("Top 10 Products by Revenue")
        plt.xlabel("Total Revenue ($)")
        plt.ylabel("Product")

    save_chart("top_10_products.png", draw, title="Top 10 Products by Revenue")


# ============================================================
# CHART 3: REVENUE BY AGE GROUP
# ============================================================

def chart_revenue_by_age_group(engine: Engine) -> None:
    """Bar chart of total revenue per age group."""
    query = """
        SELECT
            age_group,
            SUM(purchase_amount) AS total_revenue
        FROM customer
        GROUP BY age_group
        ORDER BY total_revenue DESC;
    """

    df = run_query(engine, query, label="revenue_by_age_group")

    def draw() -> None:
        plt.figure(figsize=(10, 6))
        plt.bar(df["age_group"], df["total_revenue"])
        plt.title("Revenue by Age Group")
        plt.xlabel("Age Group")
        plt.ylabel("Total Revenue ($)")

    save_chart("revenue_by_age_group.png", draw, title="Revenue by Age Group")


# ============================================================
# CHART 4: DISCOUNT EFFECTIVENESS
# ============================================================

def chart_discount_effectiveness(engine: Engine) -> None:
    """Bar chart comparing average purchase with vs without discount."""
    query = """
        SELECT
            discount_applied,
            AVG(purchase_amount) AS average_purchase
        FROM customer
        GROUP BY discount_applied;
    """

    df = run_query(engine, query, label="discount_effectiveness")

    def draw() -> None:
        plt.figure(figsize=(7, 5))
        plt.bar(df["discount_applied"], df["average_purchase"])
        plt.title("Average Purchase: Discount vs No Discount")
        plt.xlabel("Discount Applied")
        plt.ylabel("Average Purchase ($)")

    save_chart(
        "discount_effectiveness.png",
        draw,
        title="Average Purchase: Discount vs No Discount",
    )


# ============================================================
# CHART 5: REVENUE BY SEASON
# ============================================================

def chart_revenue_by_season(engine: Engine) -> None:
    """Bar chart of total revenue per season."""
    query = """
        SELECT
            season,
            SUM(purchase_amount) AS total_revenue
        FROM customer
        GROUP BY season
        ORDER BY total_revenue DESC;
    """

    df = run_query(engine, query, label="revenue_by_season")

    def draw() -> None:
        plt.figure(figsize=(8, 5))
        plt.bar(df["season"], df["total_revenue"])
        plt.title("Revenue by Season")
        plt.xlabel("Season")
        plt.ylabel("Total Revenue ($)")

    save_chart("revenue_by_season.png", draw, title="Revenue by Season")


# ============================================================
# CHART 6: SUBSCRIPTION ANALYSIS
# ============================================================

def chart_subscription_analysis(engine: Engine) -> None:
    """Bar chart of average purchase by subscription status."""
    query = """
        SELECT
            subscription_status,
            AVG(purchase_amount) AS average_purchase
        FROM customer
        GROUP BY subscription_status;
    """

    df = run_query(engine, query, label="subscription_analysis")

    def draw() -> None:
        plt.figure(figsize=(7, 5))
        plt.bar(df["subscription_status"], df["average_purchase"])
        plt.title("Average Purchase by Subscription Status")
        plt.xlabel("Subscription Status")
        plt.ylabel("Average Purchase ($)")

    save_chart(
        "subscription_analysis.png",
        draw,
        title="Average Purchase by Subscription Status",
    )


# ============================================================
# PIPELINE
# ============================================================

CHART_TASKS: list[tuple[str, Callable[[Engine], None]]] = [
    ("Revenue by Category", chart_revenue_by_category),
    ("Top 10 Products", chart_top_products),
    ("Revenue by Age Group", chart_revenue_by_age_group),
    ("Discount Effectiveness", chart_discount_effectiveness),
    ("Revenue by Season", chart_revenue_by_season),
    ("Subscription Analysis", chart_subscription_analysis),
]


def generate_all_charts(engine: Engine) -> None:
    """
    Run every chart task sequentially.

    Parameters
    ----------
    engine : Engine
        Active SQLAlchemy engine.
    """
    for name, task in CHART_TASKS:
        logger.info("---- %s ----", name)
        task(engine)


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    """
    Entry point for chart generation.

    Returns
    -------
    int
        Exit code: 0 for success, 1 for failure.
    """
    logger.info("Starting chart generation pipeline.")

    try:
        database_url = get_database_url()
        engine = create_db_engine(database_url)

        generate_all_charts(engine)

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
        logger.error("Database error while generating charts: %s", exc)
        return 1

    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error: %s", exc)
        return 1

    logger.info("All charts generated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())