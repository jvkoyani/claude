# VolHedge Pro - Options Volatility Hedging & Greeks Trading Terminal

A complete, production-ready trading terminal for options volatility hedging, Greeks risk management, and live trading integrated with Fyers API v3.

## Features

### Core Trading Engine
- **Black-Scholes Greeks Calculation**: Delta, Gamma, Theta, Vega, Volga, Vanna with Indian RBI 7.0% risk-free rate
- **Real-Time Synthetic Futures**: ATM-based synthetic future calculation
- **SEBI/NSE SPAN + Exposure Margins**: Multi-leg margin calculation with strangle/vertical spread relief
- **Delta Neutral Rebalancing**: Automatic futures hedge recommendations
- **Live Option Chain**: 4-tier resilient 100+ strike option chain with caching

### Portfolio Management
- **Multi-Tab Support**: Switch between NIFTY, BANKNIFTY, FINNIFTY, commodities, and custom scripts
- **Net Position Consolidation**: Automatic aggregation of same-strike trades with weighted-average pricing
- **Trade History Tracking**: Individual trade execution records with dates, times, and quantities
- **Real-Time Greeks**: Live delta, gamma, vega, theta calculations per position
- **Auto-Save**: Every change persists to `saved_portfolio.json`

### User Interface
- **Institutional Dark Theme**: Professional dark-themed dashboard
- **Live WebSocket Streaming**: 300ms quote updates
- **Position Management Modal**: Add, modify, and delete positions
- **Option Chain Modal**: 30/50/80/100 strike selector with quick-add buttons
- **Trade History Modal**: Double-click any position to view execution breakdown

### Fyers API Integration
- **OAuth Authentication**: Secure token-based API access
- **REST API Wrapper**: Full v3 endpoint coverage
- **High-Speed Feed**: WebSocket 300ms quote streaming
- **Symbol Formatter**: NSE/BSE/MCX symbol resolver

## Installation

### Prerequisites
- Windows 10/11 (64-bit)
- Python 3.10, 3.11, or 3.12
- Fyers Trading & Demat Account with API v3 credentials

### Quick Start (Windows)

1. **Download** the application folder to your PC
2. **Double-click** `SETUP_AND_RUN.bat`
   - Automatically checks Python
   - Installs all dependencies
   - Launches the desktop terminal

### Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Generate Fyers API token
python generate_token.py

# Start the server
python desktop_app.py
```

## Configuration

### Fyers API Setup
1. Get API credentials from [Fyers Dashboard](https://fyers.in/)
   - Copy: App ID, Secret Key, Redirect URI
2. Run `Generate_Token.bat` or `python generate_token.py`
3. Follow the OAuth flow to get access token
4. Token auto-saves to `config.json`

### config.json
```json
{
  "app_id": "YOUR_APP_ID",
  "secret_key": "YOUR_SECRET_KEY",
  "redirect_uri": "https://www.google.com/",
  "access_token": "auto-filled-after-oauth",
  "use_mock_feed": false,
  "host": "127.0.0.1",
  "port": 8000
}
```

## Usage

### Daily Workflow

1. **Token Renewal** (Fyers tokens expire daily)
   - Double-click `Generate_Token.bat` each morning
   - Follow the OAuth prompt

2. **Launch Application**
   - Double-click `Start_VolHedge.bat`
   - Dashboard opens on `http://127.0.0.1:8000`

3. **Add Positions**
   - Click **+ Add Position** modal
   - Select instrument (CE/PE/FUT), strike, expiry, qty, price
   - Or use **📊 Live Option Chain** for quick-add

4. **Monitor Portfolio**
   - Real-time MTM, Greeks, margins in top bar
   - Delta neutral recommendation shown when needed

5. **View Trade History**
   - Double-click any position row
   - See execution breakdown with dates, times, prices

### REST API Endpoints

```
GET  /                              Main dashboard
GET  /api/portfolio                 Complete portfolio data
GET  /api/tabs                      Active scrip tabs
GET  /api/positions/{symbol}        Positions for symbol
GET  /api/option_chain/{symbol}    Option chain (50+ strikes)
GET  /api/config                    App configuration
GET  /api/rebalance/{symbol}        Delta rebalance recommendation

POST /api/positions/add             Add/scale position
POST /api/positions/clear/{symbol}  Clear all positions
POST /api/symbols/add_tab           Add scrip tab
POST /api/spot_price/{symbol}       Update spot price
POST /api/portfolio/save            Manual save
POST /api/auth/token                OAuth token exchange

DELETE /api/positions/{symbol}/{id} Remove position
DELETE /api/symbols/remove_tab/{symbol} Remove tab

WS  /ws                            Real-time WebSocket feed
```

## Project Structure

```
volhedge/
├── config.json                 # API credentials & settings
├── requirements.txt            # Python dependencies
├── main.py                     # FastAPI server
├── desktop_app.py              # PySide6 desktop launcher
├── generate_token.py           # Token generation tool
│
├── SETUP_AND_RUN.bat           # Initial setup
├── Start_VolHedge.bat          # Daily launcher
├── Generate_Token.bat          # Token generator
│
├── volhedge_engine/
│   ├── greeks.py               # Black-Scholes engine
│   ├── synthetic.py            # Synthetic future calculator
│   ├── margin.py               # SPAN + exposure margin
│   └── rebalancer.py           # Delta neutral rebalancer
│
├── fyers_service/
│   ├── auth.py                 # OAuth manager
│   ├── client.py               # REST API wrapper
│   ├── feed.py                 # WebSocket feed
│   ├── option_chain_service.py # 4-tier option chain
│   └── symbol_helper.py        # Symbol formatter
│
├── portfolio/
│   ├── portfolio_manager.py    # Portfolio & position manager
│   └── saved_portfolio.json    # Auto-saved positions
│
└── static/
    ├── index.html              # UI layout
    ├── app.js                  # JavaScript app
    └── styles.css              # Dark theme styles
```

## Greeks Calculation

All calculations use Indian RBI risk-free rate (r = 7.0%):

- **Delta**: Rate of change vs spot (∂C/∂S)
- **Gamma**: Rate of change of delta (∂²C/∂S²)
- **Theta**: Time decay per day
- **Vega**: Sensitivity to 1% IV change
- **Volga**: Second-order vega sensitivity
- **Vanna**: Joint vega-delta sensitivity

## Margin Rates (SEBI/NSE Approved)

| Segment | SPAN | Exposure |
|---------|------|----------|
| Indices (NIFTY, BANKNIFTY) | 8.25% | 2.0% |
| Commodities (GOLD, SILVERM) | 11.5% | 1.25% |
| Equities (RELIANCE, TCS) | 13.5% | 3.5% |

**Special Cases:**
- Long options: 0% margin (premium only)
- Vertical spreads: 75% relief (25% margin)
- Strangler/straddle: 1.18x multi-leg factor

## Troubleshooting

### "401 Unauthorized"
- Fyers tokens expire at midnight
- Run `Generate_Token.bat` in the morning

### "Option Chain Rate Limited"
- System automatically falls back to:
  - Tier 1: Memory cache (3s TTL)
  - Tier 2: Fyers API quotes
  - Tier 3: Batch quote synthesis
  - Tier 4: Black-76 theoretical pricing

### PySide6 GUI Not Opening
- Falls back to browser automatically
- Access at `http://127.0.0.1:8000`

## Performance

- WebSocket updates every 300ms
- Option chain caches for 3s
- Supports 100+ active positions
- Sub-second position consolidation

## Security

- OAuth 2.0 token-based authentication
- No passwords stored (tokens only)
- SSL/TLS for API communication
- Credentials isolated in `config.json`

## Support

For API documentation, visit:
- [Fyers API v3 Docs](https://api.fyers.in/api/docs)
- Black-Scholes reference: Hull, *Options, Futures, and Other Derivatives*

## License

Educational and professional trading use. Use at own risk.

---

**VolHedge Pro v1.0** | Powered by Fyers API v3 & Python FastAPI
