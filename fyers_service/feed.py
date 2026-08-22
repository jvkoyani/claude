import asyncio
import json
import websockets
from datetime import datetime
from typing import Dict, Callable, List


class LiveFeed:
    """300ms High-Frequency Live Quotes Feed via WebSocket"""

    WS_URL = "wss://api-t2.fyers.in/socket/stream"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.ws = None
        self.is_connected = False
        self.subscribed_symbols = set()
        self.quote_cache = {}
        self.callbacks = []

    def add_callback(self, callback: Callable):
        """Add callback to handle incoming quotes"""
        self.callbacks.append(callback)

    async def connect(self):
        """Establish WebSocket connection"""
        try:
            self.ws = await websockets.connect(self.WS_URL)
            self.is_connected = True

            auth_message = {
                "type": "auth",
                "token": self.access_token
            }
            await self.ws.send(json.dumps(auth_message))

            return True
        except Exception as e:
            print(f"Connection error: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Close WebSocket connection"""
        if self.ws:
            await self.ws.close()
        self.is_connected = False

    async def subscribe(self, symbols: List[str]):
        """Subscribe to symbols"""
        if not self.is_connected:
            return

        if isinstance(symbols, str):
            symbols = [symbols]

        for symbol in symbols:
            message = {
                "type": "subscribe",
                "symbols": [symbol]
            }
            try:
                await self.ws.send(json.dumps(message))
                self.subscribed_symbols.add(symbol)
            except:
                pass

    async def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from symbols"""
        if not self.is_connected:
            return

        if isinstance(symbols, str):
            symbols = [symbols]

        for symbol in symbols:
            message = {
                "type": "unsubscribe",
                "symbols": [symbol]
            }
            try:
                await self.ws.send(json.dumps(message))
                self.subscribed_symbols.discard(symbol)
            except:
                pass

    async def listen(self):
        """Listen for incoming messages"""
        while self.is_connected:
            try:
                message = await asyncio.wait_for(self.ws.recv(), timeout=300)
                data = json.loads(message)

                self._process_quote(data)

                for callback in self.callbacks:
                    try:
                        callback(data)
                    except:
                        pass

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Listen error: {e}")
                self.is_connected = False
                break

    def _process_quote(self, data: Dict):
        """Process incoming quote data"""
        if 'symbol' in data:
            self.quote_cache[data['symbol']] = {
                'ltp': data.get('ltp', 0),
                'bid': data.get('bid', 0),
                'ask': data.get('ask', 0),
                'volume': data.get('volume', 0),
                'timestamp': datetime.now().isoformat()
            }

    def get_quote(self, symbol: str):
        """Get cached quote for symbol"""
        return self.quote_cache.get(symbol, {})

    def get_all_quotes(self):
        """Get all cached quotes"""
        return self.quote_cache.copy()


class MockFeed:
    """Mock feed for testing without real WebSocket"""

    def __init__(self):
        self.quote_cache = {}
        self.is_connected = False
        self.callbacks = []

    def add_callback(self, callback: Callable):
        self.callbacks.append(callback)

    async def connect(self):
        self.is_connected = True
        return True

    async def disconnect(self):
        self.is_connected = False

    async def subscribe(self, symbols):
        pass

    async def unsubscribe(self, symbols):
        pass

    def update_quote(self, symbol: str, ltp: float, bid: float = 0, ask: float = 0):
        """Update cached quote (for mock testing)"""
        data = {
            'symbol': symbol,
            'ltp': ltp,
            'bid': bid or ltp - 1,
            'ask': ask or ltp + 1,
            'timestamp': datetime.now().isoformat()
        }
        self.quote_cache[symbol] = data

        for callback in self.callbacks:
            try:
                callback(data)
            except:
                pass

    def get_quote(self, symbol: str):
        return self.quote_cache.get(symbol, {})

    def get_all_quotes(self):
        return self.quote_cache.copy()
