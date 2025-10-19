import json
import csv

# Keys to exclude from the output
EXCLUDED_KEYS = {
    "tags", "escrow", "escrowCurrency", "discretionaryType",
    "principal", "principalCurrency", "quantity"
    }

# Read JSON file
with open('transactions.json', 'r') as f:
    data = json.load(f)

if data:
    # Collect all unique keys from all entries
    keys = set()
    for item in data:
        keys.update(item.keys())

    # Remove excluded keys
    keys = keys - EXCLUDED_KEYS

    # Sort for consistent column order
    keys = sorted(keys)

    # Write to CSV
    with open('transactions.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)

    print(f"Successfully converted {len(data)} records to transactions.csv")
    print(f"Columns: {', '.join(keys)}")
