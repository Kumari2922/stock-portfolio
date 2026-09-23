import pandas as pd
import sqlite3

# Connect to your existing database (it's inside data/processed)
conn = sqlite3.connect("data/processed/stock_portfolio.db")

# --- Load your actual cleaned files ---
stock_df = pd.read_csv("data/processed/stock_prices_clean.csv")
company_df = pd.read_csv("data/processed/company_master.csv")
portfolio_raw = pd.read_excel("data/raw/Stock_Portfolio_Investment_Allocation.xlsx")

# --- Reshape portfolio data to match the Portfolio table structure ---
portfolio_df = pd.DataFrame({
    "Ticker": portfolio_raw["Ticker"],
    "Number_of_Shares": None,          # not available in source data
    "Purchase_Price": None,            # not available in source data
    "Investment_Amount": portfolio_raw["Investment (CAD)"]
})

# --- Push each DataFrame into its matching table ---
stock_df.to_sql("Stock_Prices", conn, if_exists="replace", index=False)
company_df.to_sql("Company_Master", conn, if_exists="replace", index=False)
portfolio_df.to_sql("Portfolio", conn, if_exists="replace", index=False)

conn.close()

print("Data loaded successfully!")
