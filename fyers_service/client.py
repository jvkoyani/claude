import requests
import json
from typing import Optional, Dict, List


class FyersClient:
    """Fyers REST API v3 Wrapper"""

    BASE_URL = "https://api-t2.fyers.in/api/v3"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def _request(self, method: str, endpoint: str, data=None, params=None):
        """Make HTTP request to Fyers API"""
        try:
            url = f"{self.BASE_URL}/{endpoint}"

            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            else:
                return None

            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f"HTTP {response.status_code}", 'message': response.text}
        except Exception as e:
            return {'error': str(e)}

    def get_profile(self):
        """Get user profile information"""
        return self._request("GET", "user/profile")

    def get_holdings(self):
        """Get user holdings"""
        return self._request("GET", "holdings")

    def get_positions(self):
        """Get current open positions"""
        return self._request("GET", "positions")

    def get_quote(self, symbols: List[str]):
        """Get live quote for symbols"""
        if isinstance(symbols, str):
            symbols = [symbols]

        params = {"symbols": ",".join(symbols)}
        return self._request("GET", "quotes", params=params)

    def get_depth(self, symbol: str):
        """Get market depth (order book) for symbol"""
        params = {"symbols": symbol}
        return self._request("GET", "market/depth", params=params)

    def get_option_chain(self, symbol: str, strike_count: int = 50):
        """Get option chain for symbol"""
        params = {"symbols": symbol, "strike_count": strike_count}
        return self._request("GET", "market/option-chain", params=params)

    def get_historical_data(self, symbol: str, resolution: str = "1m", date_format: str = "1"):
        """Get historical data"""
        params = {
            "symbols": symbol,
            "resolution": resolution,
            "date_format": date_format
        }
        return self._request("GET", "quotes/historical", params=params)

    def place_order(self, order_data: Dict):
        """
        Place an order
        order_data: {
            "symbol": "NSE:NIFTY24AUG24200CE",
            "qty": 1,
            "type": 1 (market) or 2 (limit),
            "side": 1 (buy) or -1 (sell),
            "productType": "MIS" or "NRML",
            "priceType": "0" (market) or "1" (limit),
            "price": 100.0
        }
        """
        return self._request("POST", "orders/place", data=order_data)

    def cancel_order(self, order_id: str):
        """Cancel an order"""
        data = {"id": order_id}
        return self._request("POST", "orders/cancel", data=data)

    def modify_order(self, order_id: str, order_data: Dict):
        """Modify an existing order"""
        order_data['id'] = order_id
        return self._request("POST", "orders/modify", data=order_data)

    def get_orders(self):
        """Get all orders"""
        return self._request("GET", "orders")

    def get_trades(self):
        """Get all trades"""
        return self._request("GET", "trades")

    def validate_token(self):
        """Validate if access token is valid"""
        try:
            result = self.get_profile()
            return 'error' not in result
        except:
            return False
