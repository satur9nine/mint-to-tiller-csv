import pandas as pd
from datetime import datetime, date
import re
import uuid

# ========== CONFIGURATION SECTION ==========
# Adjust these mappings and transformations as needed

INPUT_FILE = "transactions.csv"
OUTPUT_FILE = "transformed_transactions.csv"

# Column mapping: input → output
COLUMN_MAP = {
    "postedDate": "Date Added",
    "description": "Full Description",
    "categoryName": "Category Hint",
    "accountName": "Account",
    "amount": "Amount",
}

# Fixed output columns (columns that don't come from input)
FIXED_COLUMNS = {
    "Source": "Mint",
    "Categorized By": "",
    "Categorized Date": "",
    "Check Number": "",
    "Transaction ID": None,
    "Account ID": None,
    "Category": "",
    "Date": None,            # to be derived from postedDate
    "Description": None,     # to be derived from description
    "Month": None,           # computed
    "Week": None,            # computed
    "Account #": None,       # derived
    "Institution": None,     # derived
}

# ========== TRANSFORMATION LOGIC ==========

def collapse_multiple_spaces_to_two(text):
  """
  Collapses runs of multiple spaces in a string to exactly two spaces.

  Args:
    text: The input string.

  Returns:
    The string with multiple spaces collapsed to two spaces.
  """
  return re.sub(r' {2,}', '  ', text)

def derive_account_number(account_name):
    """Extract last 4 digits as account number if available."""
    import re
    match = re.search(r"(\d{4})$", account_name)
    return f"xxxx{match.group(1)}" if match else ""

def derive_institution(account_name: str):
    """Attempt to infer financial institution name."""
    if account_name.startswith("Adv Plus Banking"):
        return "Bank of America"

    if account_name.startswith("Unlimited Cash Rewards Visa Signature"):
        return "Bank of America"

    known_institutions = ["Bank of America", "Wells Fargo", "Chase", "American Express", "Merrill Lynch", "Capital One", "Vanguard", "HSA Bank", "Citi"]
    for name in known_institutions:
        if name.lower() in account_name.lower():
            return name.strip()
    return "Unknown"

def strip(text):
    return collapse_multiple_spaces_to_two(text.strip())

def format_amount(amount, transaction_type):
    """Ensure correct sign based on transaction type."""
    if transaction_type.upper() == "DEBIT":
        return -abs(amount)
    else:
        return abs(amount)

# ========== MAIN PROCESS ==========

def transform_transactions(input_file=INPUT_FILE, output_file=OUTPUT_FILE):
    df = pd.read_csv(input_file)
    # Start building new dataframe with all required columns
    out_cols = [
        "Date", "Description", "Category", "Amount", "Account", "Account #", "Institution",
        "Month", "Week", "Transaction ID", "Account ID", "Check Number", "Full Description",
        "Date Added", "Category Hint", "Categorized By", "Categorized Date", "Source"
    ]

    output_df = pd.DataFrame(columns=out_cols)

    # Map and transform fields
    output_df["Full Description"] = df["description"].apply(strip)
    output_df["Account"] = df["accountName"].apply(strip)
    output_df["Category Hint"] = df["categoryName"].apply(strip)

    # Added today
    today = date.today()
    output_df["Date Added"] = f"{today.month}/{today.day}/{today.year}"

    # Handle amount and sign
    output_df["Amount"] = [
        format_amount(a, t) for a, t in zip(df["amount"], df["transactionType"])
    ]

    # Derive other fields
    output_df["Date"] = pd.to_datetime(df["postedDate"]).dt.strftime("%-m/%-d/%Y")
    output_df["Description"] = df["description"].apply(strip)
    output_df["Account #"] = df["accountName"].apply(derive_account_number)
    output_df["Institution"] = df["accountName"].apply(derive_institution)

    # Month and Week from postedDate
    output_df["Month"] = pd.to_datetime(df["postedDate"]).dt.to_period("M").apply(lambda x: f"{x.start_time:%-m/1/%y}")
    output_df["Week"] = pd.to_datetime(df["postedDate"]).dt.to_period("W").apply(lambda x: f"{x.start_time:%-m/%-d/%y}")

    # Fixed and empty columns
    output_df["Category"] = ""
    output_df["Categorized By"] = ""
    output_df["Categorized Date"] = ""
    output_df["Check Number"] = ""
    output_df["Source"] = "Mint"

    # Reorder columns
    output_df = output_df[out_cols]

    # Save output
    output_df.to_csv(output_file, index=False)
    print(f"Transformed file saved to {output_file}")


if __name__ == "__main__":
    transform_transactions()
