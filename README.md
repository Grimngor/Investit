# InvestIt - Personal Portfolio Tracker

InvestIt is a personal investing web application designed for tracking passive index funds, ETFs, and cryptocurrencies. It focuses on simplicity, privacy, and accurate performance metrics.

## 🚀 Quick Start

### 1. Prerequistes
- **Python 3.12+**
- **Node.js 18+**
- (Optional) **Windows** for scheduled task support

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/your-repo/investit.git
cd investit

# Setup Backend
cd backend
python -m venv venv
./venv/Scripts/Activate.ps1  # Windows
pip install -r requirements.txt

# Setup Frontend
cd ../frontend
npm install
```

### 3. Launching
Use the provided PowerShell scripts for a seamless experience:
- `.\start-fullstack.ps1`: Launches both Backend and Frontend.
- `.\stop-all.ps1`: Safely stops all servers.

## 🏗️ Architecture

- **Backend**: FastAPI (Python) - Handles complex calculations, price fetching, and WebSocket updates.
- **Frontend**: Vue 3 + Vite + TailwindCSS - A responsive and dynamic dashboard.
- **Database**: Server-side JSON with atomic writes (StorageService).
- **Pricing**: Hybrid approach using `yfinance`, `mstarpy`, and `yahooquery`.

## 📚 Documentation Index

- [Developer Guide](docs/DEVELOPER_GUIDE.md): Script usage, testing, and formatting.
- [PRD (v2)](INVESTIT_PRD.md): Detailed project requirements and data model.
- [WebSocket Events](docs/README_WEBSOCKET_EVENTS.md): Real-time API documentation.
- [Monthly Setup](MONTHLY_UPDATE_SETUP.md): Windows Task Scheduler configuration.
- [Logging](docs/LOGGING.md): How logging works in both Backend and Frontend.

## 📊 Core Features
- **CSV Import**: Support for Spanish bank CSV formats.
- **Historical Tracking**: Accurate gain/loss based on execution-day market prices.
- **Real-time Observability**: Built-in metrics and health monitoring (`/health`).
- **Allocations**: Geographic and sector breakdowns for funds and ETFs.

---
*Created by [Javi] - Focus on private, reliable investing tracking.*
