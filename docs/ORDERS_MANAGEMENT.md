# Orders Management

## Overview

Orders are the source of truth for holdings and dashboard calculations. Current holdings are recomputed from finalized buy and sell orders.

Finalized orders are sorted chronologically before position and cost-basis calculations. This keeps invested amount and average-cost results stable even if JSON order changes.

## Manual Orders

Manual orders are created from the Portfolio page.

Required fields:

- Date: `YYYY-MM-DD`
- ISIN or crypto symbol
- Amount in EUR
- Shares or units
- Status

The backend stores `price_per_share` as `amount_eur / shares` when no explicit execution price is supplied.

## CSV Import

The Portfolio page supports importing Spanish bank CSV files with a preview step.

Supported headers:

```text
Fecha de la orden;ISIN;Importe neto;Nº de participaciones;Estado
```

Also accepted:

- `Importe estimado` or `Importe`
- common mojibake variants of `Nº de participaciones`
- semicolon or comma delimiters

CSV rules:

- Date input: `DD/MM/YYYY`
- Stored date: `YYYY-MM-DD`
- Amounts can use `,` or `.` decimals and may include `EUR`
- Negative amounts become sell orders
- Shares are stored as positive numbers
- `Estado = Rechazada` rows are skipped
- Invalid rows produce row-level errors

## Orders Page

The Orders page supports:

- Viewing index fund and crypto orders separately
- Editing one order
- Deleting one order
- Selecting and deleting multiple orders
- Deleting all orders
- Refreshing order data

## API Endpoints

- `GET /api/orders/`
- `POST /api/orders/`
- `GET /api/orders/{order_id}`
- `PUT /api/orders/{order_id}`
- `DELETE /api/orders/{order_id}`
- `DELETE /api/orders/all`
- `POST /api/orders/import-csv`

All endpoints require a bearer token.

## Troubleshooting

- Import fails with missing headers: verify the header row and delimiter.
- Holdings do not change: confirm the order status is `Finalizada`.
- Invested amount looks wrong: verify the order dates are valid `YYYY-MM-DD`, `DD/MM/YYYY`, or `DD-MM-YYYY` values so chronological cost-basis logic can sort them correctly.
- A sell does not reduce holdings: confirm `order_type` is `sell`.
- E2E import tests should write CSV files to Playwright output paths, not tracked project files.
