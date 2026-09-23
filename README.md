# Customer Purchase Analytics

End-to-end data analytics pipeline that connects to a **Neon PostgreSQL**
database, runs business-intelligence queries, generates executive reports,
produces visualizations, and exports data for **Power BI**.

Built as a CEO-level business intelligence deliverable covering revenue,
product, customer, geographic, and loyalty analysis.

---

## 🎯 Overview

This project provides a complete analytics workflow for a customer
purchase dataset hosted on Neon (serverless PostgreSQL). It is designed
to be:

- **Reproducible** — one `.env` file drives every script
- **Production-safe** — proper logging, error handling, and exit codes
- **Power BI ready** — clean CSV exports with UTF-8 BOM encoding
- **Portfolio-quality** — clean structure, docstrings, and type hints

Three standalone scripts cover the full analytics lifecycle:

| Script | Purpose |
|--------|---------|
| `analysis.py` | SQL business analysis + CEO executive report |
| `charts.py` | 6 business-intelligence charts (PNG) |
| `export_data.py` | CSV export for Power BI ingestion |


---

## ✨ Features

- 🔌 **Neon-optimized connection** — handles `channel_binding`,
  `postgres://` → `postgresql://`, SSL, and serverless autosuspend
- 📊 **16 business queries** covering revenue, products, demographics,
  geography, loyalty, discounts, and seasonality
- 📈 **6 auto-generated charts** saved as high-DPI PNGs
- 🧾 **CEO executive summary** with 8 strategic recommendations
- 📤 **Power BI CSV export** with `utf-8-sig` encoding for Windows
- 🪵 **Structured logging** with timestamps and severity levels
- 🛡️ **Robust error handling** — env, connection, DB, and generic errors
- 🔐 **Zero hardcoded secrets** — all credentials via environment variables
- 🖥️ **Cross-platform** — works on Windows, macOS, and Linux

---

## 📁 Project Structure

```
customer-purchase-analytics/
│
├── .env                      # Your Neon DATABASE_URL (never committed)
├── .env.example              # Safe template for teammates
├── .gitignore                # Excludes secrets, venv, outputs
├── requirements.txt          # Python dependencies
├── README.md                 # This file
│
├── analysis.py               # Full SQL analysis + CEO report
├── charts.py                 # 6 business charts
├── export_data.py            # CSV export for Power BI
│
└── (generated outputs — not committed)
    ├── customer_powerbi.csv
    ├── revenue_by_category.png
    ├── top_10_products.png
    ├── revenue_by_age_group.png
    ├── discount_effectiveness.png
    ├── revenue_by_season.png
    └── subscription_analysis.png
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| **Language** | Python 3.10+ |
| **Database** | Neon (serverless PostgreSQL) |
| **DB Driver** | psycopg2-binary |
| **ORM / Engine** | SQLAlchemy 2.x |
| **Data Manipulation** | pandas 2.x |
| **Visualization** | matplotlib 3.x |
| **Config** | python-dotenv |
| **BI Tool** | Microsoft Power BI |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10 or newer** — [Download](https://www.python.org/downloads/)
- **A Neon account** — [Sign up free](https://neon.tech)
- **A PostgreSQL table named `customer`** with these columns:

| Column | Type | Example |
|--------|------|---------|
| `customer_id` | integer | 101 |
| `purchase_amount` | numeric | 59.99 |
| `category` | text | Clothing |
| `item_purchased` | text | T-shirt |
| `age_group` | text | 25-34 |
| `gender` | text | Male |
| `location` | text | California |
| `season` | text | Spring |
| `subscription_status` | text | Yes / No |
| `discount_applied` | text | Yes / No |
| `shipping_type` | text | Standard |
| `review_rating` | numeric | 4.5 |
| `previous_purchases` | integer | 12 |
| `frequency_of_purchases` | text | Monthly |
| `purchase_frequency_days` | integer | 30 |

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/bilal-157/customer-purchase-analytics.git
cd customer-purchase-analytics
```

**2. Create a virtual environment**

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1

# Windows (cmd)
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

### Configuration

**1. Copy the environment template**

```bash
cp .env.example .env
```

**2. Edit `.env` and paste your Neon connection string**

```env
DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
```

Get this from your **Neon dashboard → Connection Details**.

**3. Verify the connection**

```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('OK' if os.getenv('DATABASE_URL') else 'MISSING')"
```

> If you see `OK`, your `.env` is configured correctly.

---

## 💻 Usage

### Run the full analysis

```bash
python analysis.py
```

Outputs a 16-section report plus a CEO executive summary with
strategic recommendations.

### Generate all charts

```bash
python charts.py
```

Saves 6 PNG files to the project folder.

### Export data for Power BI

```bash
python export_data.py
```

Saves `customer_powerbi.csv` ready for Power BI ingestion.

### Run all three in sequence

```bash
# macOS / Linux
python analysis.py && python charts.py && python export_data.py

# Windows PowerShell
python analysis.py; python charts.py; python export_data.py
```

---

## 📤 Outputs

### Analysis Report (`analysis.py`)

Prints to console:

- 16 numbered sections covering every business dimension
- Overall KPIs, category revenue, top/bottom products, discount impact,
  subscription, age, gender, frequency, loyalty, season, location,
  shipping, ratings, and top segments
- CEO executive summary with 8 strategic recommendations
- Data limitations disclosure

### Charts (`charts.py`)

| File | Description |
|------|-------------|
| `revenue_by_category.png` | Revenue per product category |
| `top_10_products.png` | Top 10 products by revenue |
| `revenue_by_age_group.png` | Revenue per age group |
| `discount_effectiveness.png` | Avg purchase: discount vs no discount |
| `revenue_by_season.png` | Revenue per season |
| `subscription_analysis.png` | Avg purchase by subscription status |

### Power BI Export (`export_data.py`)

- `customer_powerbi.csv` — UTF-8 BOM encoded, no index column
- Ready to load via **Power BI → Get Data → Text/CSV**

---

## 📊 Analysis Modules

### Overall KPIs
Total revenue, average purchase, min/max purchase, transaction count,
unique customer count.

### Product Analysis
Revenue by category, top 10 products, bottom 10 products.

### Customer Demographics
Age group, gender, purchase frequency, loyalty segmentation
(New / Regular / Loyal).

### Geographic Analysis
Top locations by revenue, high-value locations (with ≥ 20 customers).

### Behavioral Analysis
Discount effectiveness, subscription impact, shipping type preferences,
seasonal revenue patterns, product review ratings.

### Executive Recommendations
8 CEO-level strategic recommendations derived from query results:

1. Invest in high-performing categories
2. Promote best-selling products
3. Target high-value customer segments
4. Increase purchase frequency
5. Use targeted (not blanket) discounts
6. Invest in high-potential locations
7. Prepare for strong sales seasons
8. Protect customer retention

---

## 🏗 Architecture

```
┌─────────────────┐
│   Neon Postgres │
│   (cloud DB)    │
└────────┬────────┘
         │  SSL / psycopg2
         ▼
┌─────────────────────────────┐
│   SQLAlchemy Engine         │
│   - pool_pre_ping           │
│   - pool_recycle=300        │
│   - sslmode=require         │
└────────┬────────────────────┘
         │
    ┌────┴──────┬──────────────┐
    ▼           ▼              ▼
┌────────┐ ┌─────────┐  ┌──────────────┐
│analysis│ │ charts  │  │export_data   │
│  .py   │ │  .py    │  │    .py       │
└────┬───┘ └────┬────┘  └──────┬───────┘
     │          │              │
     ▼          ▼              ▼
┌─────────┐ ┌────────┐  ┌──────────────┐
│ Console │ │  PNGs  │  │ CSV → PowerBI│
│ Report  │ │        │  │              │
└─────────┘ └────────┘  └──────────────┘
---

## 📄 License

This project is licensed under the **MIT License**.
 
```
MIT License

Copyright (c) 2026 Muhammad Bilal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

---

## 🙏 Acknowledgments

- [Neon](https://neon.tech) — serverless PostgreSQL hosting
- [pandas](https://pandas.pydata.org/) — data manipulation
- [SQLAlchemy](https://www.sqlalchemy.org/) — database toolkit
- [matplotlib](https://matplotlib.org/) — visualization
- [Power BI](https://powerbi.microsoft.com/) — business intelligence

---

## 📬 Contact

**Muhammad Bilal**
- GitHub: [@bilal-157](https://github.com/bilal-157)
- LinkedIn: [muhammadbilal711](https://www.linkedin.com/in/muhammadbilal711)
- Email: rafiqueb087@gmail.com

---

⭐ If you found this project useful, consider giving it a star!
