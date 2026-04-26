# WebSocket Events (InvestIt)

Real-time events emitted by the backend (all JSON include ISO UTC `timestamp`).

| Event Type        | Description                                      | Payload Keys                                     |
| ----------------- | ------------------------------------------------ | ------------------------------------------------ |
| connection_status | Initial handshake after successful auth         | type, status, client_id, timestamp               |
| pong              | Response to client `ping`                       | type, timestamp                                  |
| order_created     | A manual order was created                      | type, order_id, timestamp                        |
| order_updated     | A manual order was updated                      | type, order_id, timestamp                        |
| order_deleted     | A manual order was deleted                      | type, order_id, timestamp                        |
| orders_imported   | Bulk import completed (CSV)                     | type, count, timestamp                           |
| prices_updated    | Background price fetch completed                | type, count, timestamp                           |

## Usage Notes
- Subscribe with a valid JWT using `ws://<host>/ws?token=<access_token>`.
- Send `{"type": "ping"}` to receive a `pong`.
- Importing CSV triggers `orders_imported` once parsing completes.
- Manual CRUD operations produce single-item lifecycle events.

Extend this document if new event types are added.
