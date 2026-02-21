# Orders Management Guide

## Overview

The Orders tab provides complete management of your investment orders with support for editing, deleting, and bulk import via CSV files.

## Viewing Orders

All your executed orders are displayed in a sortable table showing:
- **Date**: Execution date (DD/MM/YYYY)
- **ISIN**: 12-character instrument identifier
- **Ticker**: Optional ticker symbol
- **Shares**: Number of shares/units purchased
- **Amount (EUR)**: Total order cost
- **Price**: Calculated price per share
- **Status**: Order status (Finalizada/Rechazada)

## Editing Orders

To modify an existing order:

1. Click the **edit icon** (pencil) in the Actions column
2. The Edit Order modal will open with the current order details
3. Modify any of the following fields:
   - Order Date (date picker)
   - ISIN (12-character code)
   - Ticker (optional)
   - Amount in EUR
   - Number of Shares
   - Order Type (Buy/Sell)
   - Status (Finalizada/Rechazada)
   - Notes (optional text)
4. The price per share is **automatically calculated** from amount ÷ shares
5. Click **Save Changes** to update the order
6. The order list will refresh automatically

### Validation Rules

- ISIN must be exactly 12 characters
- Amount and Shares must be positive numbers
- Date is required

## Deleting Orders

### Single Order
Click the **delete icon** (trash) in the Actions column and confirm the deletion.

### All Orders
Use the **Delete All** button at the top right to remove all orders at once. A confirmation prompt will appear.

## CSV Import with Preview & Edit

InvestIt supports importing multiple orders from a CSV file with an interactive preview feature.

### Step 1: Select CSV File

1. Navigate to the Portfolio view
2. Locate the **Import Orders from CSV** section
3. Either:
   - Drag and drop your `.csv` file onto the drop zone
   - Click the drop zone to browse and select a file

### Step 2: Preview & Edit Orders

After selecting a CSV file:

1. Click **Preview & Import**
2. A preview modal opens showing all parsed orders in a table
3. Review each order for accuracy
4. **Edit any row** by clicking the edit icon (pencil):
   - Inline editing allows you to change Date, ISIN, Amount, Shares, or Status
   - Click the checkmark to save edits or X to cancel
5. **Remove unwanted rows** by clicking the delete icon (trash)
6. The bottom bar shows the total count of orders ready to import

### Step 3: Import Orders

Once you're satisfied with the preview:

1. Click **Import Orders** at the bottom right
2. The backend will process all orders
3. A success toast will show the number of imported orders
4. Your portfolio will refresh automatically
5. Navigate to the Orders tab to see the new entries

### Expected CSV Format

Your CSV file should contain the following columns (header row required):

```
Fecha de la orden;ISIN;Importe estimado;Nº de participaciones;Estado
```

**Supported Delimiters**: Both comma (`,`) and semicolon (`;`) are detected automatically.

**Example**:
```csv
Fecha de la orden;ISIN;Importe estimado;Nº de participaciones;Estado
25/10/2025;IE00B4L5Y983;850.50;10;Finalizada
26/10/2025;LU0274208692;1200.00;5;Finalizada
```

**Column Details**:
- **Fecha de la orden**: Date in DD/MM/YYYY format
- **ISIN**: 12-character instrument identifier
- **Importe estimado**: Total order amount in EUR (use `.` or `,` as decimal separator)
- **Nº de participaciones**: Number of shares/units
- **Estado**: Order status (`Finalizada` or `Rechazada`)

### CSV Import Notes

- Invalid rows (missing data, malformed ISIN, etc.) are skipped
- Only orders with status `Finalizada` contribute to portfolio holdings
- Duplicate orders are allowed (the system does not deduplicate)
- After import, you can edit or delete orders individually from the Orders tab

## Keyboard Shortcuts

- **Esc**: Close any open modal (edit or preview)
- **Enter**: Submit form when editing an order (if valid)

## Tips

- **Price Calculation**: The system automatically calculates price per share when you enter amount and shares. This helps catch data entry errors.
- **Bulk Edit**: Use the CSV preview to batch-edit multiple orders before importing rather than editing them one-by-one after import.
- **Status Filtering**: Only `Finalizada` orders count toward your portfolio holdings. Mark test or cancelled orders as `Rechazada`.
- **Data Safety**: The Delete All button provides a confirmation prompt to prevent accidental data loss.

## Troubleshooting

### CSV Import Fails
- Ensure your CSV has a header row with the expected column names
- Check that ISINs are exactly 12 characters
- Verify amounts and shares are positive numbers
- Try using semicolon (`;`) as the delimiter if comma doesn't work

### Edit Modal Won't Save
- Confirm the ISIN is exactly 12 characters
- Ensure Amount and Shares are greater than zero
- Check that a valid date is selected

### Orders Not Appearing in Portfolio
- Only orders with status `Finalizada` are included in holdings calculations
- Refresh the Portfolio view to see updated totals
- Check the Orders tab to verify the order was saved correctly
