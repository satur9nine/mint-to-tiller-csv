import pandas as pd
from datetime import datetime, date
import re

# ========== CONFIGURATION SECTION ==========
INPUT_FILE = "transactions.csv"
OUTPUT_FILE = "transformed_transactions.csv"
DISCARD_FILE = "discarded_transactions.csv"

# ========== TRANSFORMATION LOGIC ==========

def collapse_multiple_spaces_to_two(text):
    """Collapses runs of multiple spaces in a string to exactly two spaces."""
    return re.sub(r' {2,}', '  ', text)

def derive_account_number(account_name):
    """Extract last 4 digits as account number if available."""
    match = re.search(r"(\d{4})$", account_name)
    return f"xxxx{match.group(1)}" if match else ""

def derive_institution(account_name: str):
    """Attempt to infer financial institution name."""
    if account_name.startswith("Adv Plus Banking") or account_name.startswith("Adv SafeBalance Banking"):
        return "Bank of America"

    if account_name.startswith("Unlimited Cash Rewards Visa Signature"):
        return "Bank of America"

    known_institutions = [
        "Bank of America", "Wells Fargo", "Chase", "American Express",
        "Merrill Lynch", "Capital One", "Vanguard", "HSA Bank", "Citi"
    ]
    for name in known_institutions:
        if name.lower() in account_name.lower():
            return name.strip()
    return "Unknown"

def strip(text):
    """Strip and collapse multiple spaces."""
    return collapse_multiple_spaces_to_two(text.strip())

def format_amount(amount, transaction_type):
    """Ensure correct sign based on transaction type."""
    if transaction_type.upper() == "DEBIT":
        return -abs(amount)
    else:
        return abs(amount)

def filter_pending_transactions(df):
    """
    Remove all PENDING transactions.
    Returns indices of PENDING transactions to discard.
    """
    pending_indices = df[df['status'] == 'PENDING'].index.tolist()
    return pending_indices

# ========== MAIN PROCESS ==========

def transform_transactions(input_file=INPUT_FILE, output_file=OUTPUT_FILE, discard_file=DISCARD_FILE):
    df = pd.read_csv(input_file, low_memory=False)

    print(f"Loaded {len(df)} transactions from {input_file}")

    # Remove all PENDING transactions
    pending_indices = filter_pending_transactions(df)
    pending_df = df.loc[pending_indices].copy()
    print(f"Found {len(pending_indices)} PENDING transactions")

    # Remove PENDING from main dataframe
    df = df.drop(pending_indices)

    # Filter out $0 transactions
    zero_amount_df = df[df['amount'] == 0].copy()
    df = df[df['amount'] != 0]
    print(f"Found {len(zero_amount_df)} transactions with $0 amount")

    # Combine all discarded transactions
    discarded_df = pd.concat([pending_df, zero_amount_df], ignore_index=True)
    if len(discarded_df) > 0:
        discarded_df.to_csv(discard_file, index=False)
        print(f"Saved {len(discarded_df)} discarded transactions to {discard_file}")

    print(f"Processing {len(df)} valid transactions")

    # Define output columns
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
    output_df["Month"] = pd.to_datetime(df["postedDate"]).dt.to_period("M").apply(
        lambda x: f"{x.start_time.month}/1/{x.start_time.strftime('%y')}"
    )
    output_df["Week"] = pd.to_datetime(df["postedDate"]).dt.to_period("W").apply(
        lambda x: f"{x.start_time.month}/{x.start_time.day}/{x.start_time.strftime('%y')}"
    )

    # Fixed and empty columns
    output_df["Category"] = ""
    output_df["Categorized By"] = ""
    output_df["Categorized Date"] = ""
    output_df["Check Number"] = ""
    output_df["Transaction ID"] = ""
    output_df["Account ID"] = ""
    output_df["Source"] = "Mint"

    # Reorder columns
    output_df = output_df[out_cols]

    # Save output
    output_df.to_csv(output_file, index=False)
    print(f"Transformed file saved to {output_file}")
    print(f"Successfully processed {len(output_df)} transactions")


if __name__ == "__main__":
    transform_transactions()
