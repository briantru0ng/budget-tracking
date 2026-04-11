# Upload Documents

Import bank/card statement CSVs into the transaction database. Two import methods plus automatic bank detection.

## Batch Import (Statements Folder)

Drop CSV files into the `statements/` folder, then click "Import All from Statements Folder." The system:

1. Auto-detects the bank format from CSV headers
2. Parses transactions and applies categorization rules
3. Skips duplicates already in the database
4. Moves processed files to `completed_statements/`
5. Shows per-file diagnostics (bank detected, rows parsed, added, duplicates skipped)

## Manual Upload (Drag & Drop)

Use the file uploader to select one or more CSVs. Enter a source label (e.g., "PNC Checking") to tag the transactions. Click "Import All Files" to process.

## Supported Banks

| Bank | Format Details |
|---|---|
| **PNC** | Skips credit card payments and internal transfers. Keeps Zelle, Venmo, and purchases. |
| **Capital One** | Skips own payment credits. All charges imported as expenses. |
| **Citi** | Skips payment credits. All charges imported as expenses. |
| **Discover** | Skips "Payments and Credits" category rows. All charges imported. |

Bank detection is automatic based on CSV column headers.

## Recent Uploads

A summary table at the bottom shows each source, its date range, and transaction count.

## Duplicate Handling

Duplicate detection runs automatically during import. Transactions matching an existing Date + Description + Amount combination are skipped. For deeper duplicate analysis, see Settings > Duplicates.
