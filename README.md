# Wealthily

**Your Wealth, Simplified** - A comprehensive personal finance and portfolio management application.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

### Asset Tracking
- **Mutual Funds** - Track with live NAV updates via MFAPI.in
- **Stocks** - NSE/BSE holdings with sector classification
- **Real Estate** - Properties with appreciation tracking
- **Gold & Silver** - Physical, Digital, SGB, ETFs
- **Bank Accounts** - Savings, Current accounts
- **Fixed Deposits** - FDs with maturity tracking
- **NPS** - National Pension System (Tier 1 & 2)
- **PPF & EPF** - Provident fund tracking
- **Insurance** - Term, Health, ULIP policies
- **Credit Cards** - Outstanding balance tracking
- **Loans** - EMI and outstanding amount tracking

### Financial Tools
- **Net Worth Tracker** - Monthly snapshots with historical charts
- **Future Forecast** - Project wealth growth over 5-30 years
- **Live NAV Updates** - Auto-fetch mutual fund NAVs
- **Expected Returns** - Customizable return rates per asset

### Data Storage
- **Excel (Local)** - Default mode, data stored in `.xlsx` file
- **Firebase Firestore (Cloud)** - Optional cloud storage for multi-device access
- **Import/Export** - Easy backup and restore via Excel files

## Screenshots

Dashboard showing net worth summary, asset breakdown, and quick actions.

## Installation

### Option 1: Standard Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/wealthily.git
   cd wealthily
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

5. **Open in browser**
   ```
   http://localhost:5001
   ```

### Option 2: Docker Installation

1. **Using Docker Compose (Recommended)**
   ```bash
   docker-compose up -d
   ```

2. **Using Docker directly**
   ```bash
   docker build -t wealthily .
   docker run -d -p 5001:5001 -v wealthily_data:/app/data wealthily
   ```

3. **Open in browser**
   ```
   http://localhost:5001
   ```

## Configuration

### Storage Modes

#### Excel (Default)
Data is stored locally in `data/wealthily.xlsx`. No configuration needed.

#### Firebase Firestore
1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Enable Firestore Database
3. Generate a service account key (Project Settings → Service Accounts)
4. Go to Settings in the app and upload the JSON key file
5. Install firebase-admin: `pip install firebase-admin`

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `production` |
| `FLASK_DEBUG` | Debug mode | `False` |
| `PORT` | Server port | `5001` |

### Screen Shots
<img width="945" height="443" alt="image" src="https://github.com/user-attachments/assets/69d4cb3f-9d0c-497c-96f9-ff5dd9672969" />
<img width="943" height="443" alt="image" src="https://github.com/user-attachments/assets/4305a274-b4af-4641-9cca-94352471cada" />
<img width="940" height="443" alt="image" src="https://github.com/user-attachments/assets/62eb4d30-349a-42f5-977a-fc5461c2aa4b" />




## API Integrations

### MFAPI.in (Mutual Fund NAVs)
- Free API, no authentication required
- Provides historical NAV data for Indian mutual funds
- Usage: Add scheme code when creating mutual fund entry

### Metal Prices
- Gold and silver prices fetched from metals.live API
- Converted to INR per gram

## Usage Guide

### Adding Assets
1. Click "Add New" in sidebar or use Quick Add buttons
2. Select asset type from dropdown
3. Fill in the required details
4. Click "Add Item"

### Tracking Net Worth
1. Go to "Net Worth" in sidebar
2. View current breakdown by asset class
3. Click "Save Snapshot" to record monthly data
4. View historical chart and trends

### Forecasting
1. Go to "Forecast" in sidebar
2. Select forecast period (5-30 years)
3. View projected growth based on expected returns
4. Adjust expected returns in individual assets for accuracy

### Backup & Restore
1. Go to "Settings"
2. Click "Export to Excel" to download backup
3. Use "Import" to restore from backup file

## Tech Stack

- **Backend**: Python 3.9+, Flask
- **Frontend**: Bootstrap 5, Bootstrap Icons, Chart.js
- **Storage**: Pandas, OpenPyXL (Excel), Firebase Admin SDK (optional)
- **APIs**: Requests library for external API calls

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [MFAPI.in](https://www.mfapi.in/) for free mutual fund NAV API
- [Bootstrap](https://getbootstrap.com/) for UI components
- [Chart.js](https://www.chartjs.org/) for beautiful charts
- [Freefincal](https://freefincal.com/) for inspiration on portfolio tracking features
