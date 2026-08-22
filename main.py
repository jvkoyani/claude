from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from datetime import datetime

from fyers_service.auth import FyersAuth
from fyers_service.client import FyersClient
from fyers_service.feed import MockFeed
from fyers_service.option_chain_service import OptionChainService
from portfolio.portfolio_manager import PortfolioManager
from volhedge_engine.rebalancer import RebalancerEngine


app = FastAPI(title="VolHedge Pro")

# Enable CORS for frontend running on Netlify
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Netlify domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth = FyersAuth()
portfolio_manager = PortfolioManager()

fyers_client = None
feed = MockFeed()
option_chain_service = None

active_connections = []


def initialize_services():
    """Initialize Fyers services with access token"""
    global fyers_client, option_chain_service

    token = auth.get_access_token()
    if token:
        fyers_client = FyersClient(token)
        option_chain_service = OptionChainService(fyers_client)
        return True
    return False


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    initialize_services()
    await feed.connect()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await feed.disconnect()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main trading dashboard UI"""
    try:
        with open("static/index.html", "r") as f:
            return f.read()
    except:
        return "<h1>VolHedge Pro - Trading Terminal</h1><p>Dashboard loading...</p>"


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """High-frequency duplex market streaming channel (300ms ticks)"""
    await websocket.accept()
    active_connections.append(websocket)

    async def feed_updates():
        """Send portfolio updates to client"""
        while True:
            try:
                await asyncio.sleep(0.3)

                for symbol in portfolio_manager.get_all_tabs():
                    summary = portfolio_manager.get_portfolio_summary(symbol)
                    positions = portfolio_manager.get_positions(symbol)

                    data = {
                        'type': 'portfolio_update',
                        'symbol': symbol,
                        'summary': summary,
                        'positions': positions
                    }

                    await websocket.send_json(data)

            except:
                break

    update_task = asyncio.create_task(feed_updates())

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get('type') == 'subscribe':
                symbol = message.get('symbol')
                if symbol:
                    await feed.subscribe(symbol)

            elif message.get('type') == 'unsubscribe':
                symbol = message.get('symbol')
                if symbol:
                    await feed.unsubscribe(symbol)

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        update_task.cancel()


@app.get("/api/option_chain/{symbol}")
async def get_option_chain(symbol: str, strike_count: int = 50):
    """Returns resilient 100+ strike live Option Chain"""
    if not option_chain_service:
        return {'error': 'Service not initialized'}

    try:
        spot = portfolio_manager.get_spot_price(symbol)
        chain = option_chain_service.get_option_chain(symbol, strike_count)
        enriched = option_chain_service.enrich_option_chain(chain, spot)
        return enriched
    except Exception as e:
        return {'error': str(e), 'strikes': []}


@app.post("/api/symbols/add_tab")
async def add_tab(data: dict):
    """Adds new scrip tab (auto-saves to disk)"""
    symbol = data.get('symbol', '').upper()
    if portfolio_manager.add_tab(symbol):
        return {'success': True, 'symbol': symbol}
    return {'success': False, 'error': 'Failed to add tab'}


@app.delete("/api/symbols/remove_tab/{symbol}")
async def remove_tab(symbol: str):
    """Deletes scrip tab (auto-saves to disk)"""
    if portfolio_manager.remove_tab(symbol.upper()):
        return {'success': True, 'symbol': symbol}
    return {'success': False, 'error': 'Failed to remove tab'}


@app.get("/api/portfolio")
async def get_portfolio():
    """Get complete portfolio"""
    tabs = portfolio_manager.get_all_tabs()
    portfolio_data = {}

    for tab in tabs:
        summary = portfolio_manager.get_portfolio_summary(tab)
        positions = portfolio_manager.get_positions(tab)
        portfolio_data[tab] = {
            'summary': summary,
            'positions': positions
        }

    return portfolio_data


@app.post("/api/positions/add")
async def add_position(data: dict):
    """Adds position contract or scales into existing contract"""
    symbol = data.get('symbol', '').upper()
    position_data = {
        'strike': data.get('strike'),
        'expiry': data.get('expiry'),
        'opt_type': data.get('opt_type'),
        'qty': data.get('qty'),
        'entry_price': data.get('entry_price'),
        'tag': data.get('tag', '')
    }

    if portfolio_manager.add_position(symbol, position_data):
        summary = portfolio_manager.get_portfolio_summary(symbol)
        return {'success': True, 'summary': summary}

    return {'success': False, 'error': 'Failed to add position'}


@app.delete("/api/positions/{symbol}/{pos_id}")
async def remove_position(symbol: str, pos_id: str):
    """Removes position"""
    if portfolio_manager.remove_position(symbol.upper(), pos_id):
        summary = portfolio_manager.get_portfolio_summary(symbol.upper())
        return {'success': True, 'summary': summary}

    return {'success': False, 'error': 'Position not found'}


@app.post("/api/positions/clear/{symbol}")
async def clear_positions(symbol: str):
    """Clears tab positions"""
    if portfolio_manager.clear_positions(symbol.upper()):
        return {'success': True, 'symbol': symbol}

    return {'success': False, 'error': 'Failed to clear positions'}


@app.post("/api/portfolio/save")
async def save_portfolio():
    """Manual persistence trigger"""
    portfolio_manager.save_portfolio()
    return {'success': True, 'message': 'Portfolio saved'}


@app.post("/api/portfolio/load")
async def load_portfolio():
    """Manual load trigger"""
    portfolio_data = portfolio_manager.load_portfolio()
    return portfolio_data


@app.get("/api/config")
async def get_config():
    """Get app configuration"""
    return {
        'app_id': auth.config.get('app_id', ''),
        'authenticated': auth.is_authenticated(),
        'host': auth.config.get('host', '127.0.0.1'),
        'port': auth.config.get('port', 8000)
    }


@app.post("/api/auth/token")
async def get_token_via_auth_code(data: dict):
    """Exchange auth code for access token"""
    auth_code = data.get('auth_code', '')

    if not auth_code:
        return {'success': False, 'error': 'Auth code required'}

    token = auth.exchange_code_for_token(auth_code)

    if token:
        initialize_services()
        return {'success': True, 'token': token}

    return {'success': False, 'error': 'Failed to get token'}


@app.get("/api/rebalance/{symbol}")
async def get_rebalance_recommendation(symbol: str):
    """Get delta neutral rebalancing recommendation"""
    positions = portfolio_manager.get_positions(symbol.upper())
    recommendation = RebalancerEngine.get_rebalance_recommendation(symbol.upper(), positions)
    return recommendation


@app.post("/api/spot_price/{symbol}")
async def update_spot_price(symbol: str, data: dict):
    """Update spot price for symbol"""
    price = data.get('price', 0)
    portfolio_manager.update_spot_price(symbol.upper(), price)
    return {'success': True, 'symbol': symbol, 'price': price}


@app.get("/api/tabs")
async def get_all_tabs():
    """Get all active tabs"""
    tabs = portfolio_manager.get_all_tabs()
    return {'tabs': tabs}


@app.get("/api/positions/{symbol}")
async def get_positions_for_symbol(symbol: str):
    """Get all positions for a symbol"""
    positions = portfolio_manager.get_positions(symbol.upper())
    return {'symbol': symbol, 'positions': positions}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=auth.config.get('host', '127.0.0.1'),
        port=auth.config.get('port', 8000)
    )
