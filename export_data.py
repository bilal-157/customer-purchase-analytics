"""
Customer Data Export Script
============================

Exports the `customer` table from a Neon PostgreSQL database to a CSV file
optimized for Power BI ingestion.

Environment:
    DATABASE_URL : PostgreSQL connection string (required)
                   Example: postgresql://user:pass@host/db?sslmode=require

Output:
    customer_powerbi.csv : Flattened CSV export, index-free, UTF-8 encoded.

Usage:
    python export_data.py
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_FILE = Path("customer_powerbi.csv")
SOURCE_TABLE = "customer"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


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
    Load and validate the DATABASE_URL from the environment.

    Returns
    -------
    str
        A SQLAlchemy-compatible PostgreSQL connection string.

    Raises
    ------
    EnvironmentError
        If DATABASE_URL is missing from the environment.
    """
    load_dotenv()

    url = os.getenv("DATABASE_URL")

    if not url:
        raise EnvironmentError(
            "DATABASE_URL is not set. Add it to your .env file or export it "
            "as an environment variable before running this script."
        )

    # Normalize legacy 'postgres://' scheme for SQLAlchemy 1.4+ compatibility.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # psycopg2 on Windows rejects 'channel_binding=require' emitted by Neon.
    # sslmode=require already enforces an encrypted channel.
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
        pool_pre_ping=True,      # Detect stale connections (Neon autosuspends).
        pool_recycle=300,        # Recycle connections every 5 minutes.
        pool_size=5,
        max_overflow=10,
        connect_args={
            "sslmode": "require",
            "connect_timeout": 10,
        },
        future=True,
    )


# ============================================================
# DATA EXTRACTION
# ============================================================

def fetch_data(engine: Engine, table: str) -> pd.DataFrame:
    """
    Retrieve all rows from the specified table.

    Parameters
    ----------
    engine : Engine
        Active SQLAlchemy engine.
    table : str
        Name of the source table.

    Returns
    -------
    pd.DataFrame
        The queried data as a DataFrame.
    """
    logger.info("Querying table '%s' from Neon...", table)

    query = text(f"SELECT * FROM {table};")

    with engine.connect() as connection:
        df = pd.read_sql(query, connection)

    logger.info("Retrieved %s rows and %s columns.", f"{len(df):,}", df.shape[1])

    return df


# ============================================================
# DATA EXPORT
# ============================================================

def export_to_csv(df: pd.DataFrame, output_path: Path) -> None:
    """
    Write the DataFrame to a UTF-8 CSV file without the index column.

    Parameters
    ----------
    df : pd.DataFrame
        Data to export.
    output_path : Path
        Destination file path.
    """
    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",   # BOM helps Power BI detect UTF-8 on Windows.
        na_rep="",              # Emit empty strings for NaN values.
    )

    size_kb = output_path.stat().st_size / 1024
    logger.info(
        "Exported to '%s' (%.2f KB).",
        output_path.resolve(),
        size_kb,
    )


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    """
    Orchestrate the export pipeline.

    Returns
    -------
    int
        Exit code: 0 for success, 1 for failure.
    """
    logger.info("Starting customer data export.")

    try:
        database_url = get_database_url()
        engine = create_db_engine(database_url)

        df = fetch_data(engine, SOURCE_TABLE)
        export_to_csv(df, OUTPUT_FILE)

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
        logger.error("Database error while executing the query: %s", exc)
        return 1

    except Exception as exc:  # noqa: BLE001 — top-level safety net
        logger.exception("Unexpected error: %s", exc)
        return 1

    logger.info("Export completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())