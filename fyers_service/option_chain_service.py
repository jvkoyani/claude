import json
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .symbol_helper import SymbolHelper
from volhedge_engine.greeks import GreeksCalculator
from volhedge_engine.synthetic import SyntheticEngine


class OptionChainService:
    """4-Tier Resilient 100+ Strike Option Chain Engine"""

    def __init__(self, fyers_client, cache_ttl_seconds=3):
        self.client = fyers_client
        self.cache_ttl = cache_ttl_seconds
        self.cache = {}
        self.cache_timestamps = {}

    def get_option_chain(self, symbol: str, strike_count: int = 50, use_cache: bool = True):
        """
        Retrieve option chain with 4-tier fallback:
        Tier 1: Live cache (TTL 3s)
        Tier 2: Fyers API option-chain endpoint
        Tier 3: Batch quote synthesis
        Tier 4: Black-76 theoretical pricing
        """

        cache_key = f"{symbol}_{strike_count}"

        if use_cache and cache_key in self.cache:
            if time.time() - self.cache_timestamps.get(cache_key, 0) < self.cache_ttl:
                return self.cache[cache_key]

        chain_data = self._tier1_live_cache(symbol, strike_count)
        if chain_data:
            return chain_data

        chain_data = self._tier2_fyers_api(symbol, strike_count)
        if chain_data:
            self._cache_result(cache_key, chain_data)
            return chain_data

        chain_data = self._tier3_batch_quotes(symbol, strike_count)
        if chain_data:
            self._cache_result(cache_key, chain_data)
            return chain_data

        chain_data = self._tier4_theoretical(symbol, strike_count)
        if chain_data:
            self._cache_result(cache_key, chain_data)
            return chain_data

        return {'error': 'Rate Limited - All tiers exhausted', 'strikes': []}

    def _tier1_live_cache(self, symbol: str, strike_count: int) -> Optional[Dict]:
        """Tier 1: Check live in-memory cache"""
        cache_key = f"{symbol}_{strike_count}"
        if cache_key in self.cache:
            if time.time() - self.cache_timestamps.get(cache_key, 0) < self.cache_ttl:
                return self.cache[cache_key]
        return None

    def _tier2_fyers_api(self, symbol: str, strike_count: int) -> Optional[Dict]:
        """Tier 2: Fyers API option-chain endpoint"""
        try:
            base_symbol = SymbolHelper.remove_exchange_prefix(symbol)
            response = self.client.get_option_chain(base_symbol, strike_count)

            if response and 'strikes' in response:
                return response
            return None
        except:
            return None

    def _tier3_batch_quotes(self, symbol: str, strike_count: int) -> Optional[Dict]:
        """Tier 3: Synthesize from batch quotes (high-speed fallback)"""
        try:
            base_symbol = SymbolHelper.remove_exchange_prefix(symbol)
            spot_quote = self.client.get_quote(f"NSE:{base_symbol}")

            if not spot_quote or 'error' in spot_quote:
                return None

            spot = spot_quote.get('ltp', 0)
            if not spot:
                return None

            strikes = self._generate_strike_range(spot, strike_count)
            chain_data = {
                'symbol': symbol,
                'spot': spot,
                'timestamp': datetime.now().isoformat(),
                'strikes': []
            }

            symbols_to_quote = []
            for strike in strikes:
                ce_symbol = SymbolHelper.format_option_symbol(base_symbol, strike, '26AUG24', 'CE')
                pe_symbol = SymbolHelper.format_option_symbol(base_symbol, strike, '26AUG24', 'PE')
                symbols_to_quote.extend([ce_symbol, pe_symbol])

            quotes = self.client.get_quote(symbols_to_quote)

            if quotes and 'data' in quotes:
                for strike in strikes:
                    ce_ltp = 0
                    pe_ltp = 0

                    for quote_data in quotes.get('data', {}).values():
                        if str(int(strike)) in quote_data.get('symbol', ''):
                            if 'CE' in quote_data.get('symbol', ''):
                                ce_ltp = quote_data.get('ltp', 0)
                            elif 'PE' in quote_data.get('symbol', ''):
                                pe_ltp = quote_data.get('ltp', 0)

                    if ce_ltp > 0 or pe_ltp > 0:
                        chain_data['strikes'].append({
                            'strike': strike,
                            'ce_ltp': ce_ltp,
                            'pe_ltp': pe_ltp,
                            'ce_iv': 0,
                            'pe_iv': 0
                        })

            if chain_data['strikes']:
                return chain_data
            return None
        except:
            return None

    def _tier4_theoretical(self, symbol: str, strike_count: int) -> Optional[Dict]:
        """Tier 4: Black-76 theoretical synthesizer"""
        try:
            base_symbol = SymbolHelper.remove_exchange_prefix(symbol)

            spot_quote = self.client.get_quote(f"NSE:{base_symbol}")
            if not spot_quote or 'error' in spot_quote:
                return None

            spot = spot_quote.get('ltp', 0)
            if not spot:
                return None

            strikes = self._generate_strike_range(spot, strike_count)
            chain_data = {
                'symbol': symbol,
                'spot': spot,
                'timestamp': datetime.now().isoformat(),
                'tier': 'Theoretical (Tier 4)',
                'strikes': []
            }

            T = 0.01
            sigma = 0.25

            for strike in strikes:
                ce_price = GreeksCalculator.calculate_call_price(spot, strike, T, sigma)
                pe_price = GreeksCalculator.calculate_put_price(spot, strike, T, sigma)

                chain_data['strikes'].append({
                    'strike': strike,
                    'ce_ltp': round(ce_price, 2),
                    'pe_ltp': round(pe_price, 2),
                    'ce_iv': sigma * 100,
                    'pe_iv': sigma * 100,
                    'theoretical': True
                })

            return chain_data
        except:
            return None

    def _generate_strike_range(self, spot: float, strike_count: int) -> List[float]:
        """Generate evenly-spaced strike range around spot"""
        if strike_count <= 1:
            return [spot]

        interval = 100 if spot > 10000 else 10 if spot > 1000 else 1

        half_count = strike_count // 2
        strikes = []

        for i in range(-half_count, half_count + 1):
            strike = spot + (i * interval)
            if strike > 0:
                strikes.append(strike)

        strikes = sorted(list(set([int(s / interval) * interval for s in strikes])))
        return strikes[:strike_count]

    def _cache_result(self, cache_key: str, data: Dict):
        """Cache result with timestamp"""
        self.cache[cache_key] = data
        self.cache_timestamps[cache_key] = time.time()

    def enrich_option_chain(self, chain_data: Dict, spot: float) -> Dict:
        """Enrich option chain with Greeks and IV"""
        if not chain_data or 'strikes' not in chain_data:
            return chain_data

        T = 0.01
        enriched_chain = chain_data.copy()

        for strike_data in enriched_chain.get('strikes', []):
            strike = strike_data.get('strike', 0)
            ce_ltp = strike_data.get('ce_ltp', 0)
            pe_ltp = strike_data.get('pe_ltp', 0)

            if ce_ltp > 0:
                ce_iv = GreeksCalculator.calculate_implied_volatility(spot, strike, T, ce_ltp, 'CE')
                ce_delta = GreeksCalculator.calculate_delta(spot, strike, T, ce_iv, 'CE')
                ce_gamma = GreeksCalculator.calculate_gamma(spot, strike, T, ce_iv)
                ce_vega = GreeksCalculator.calculate_vega(spot, strike, T, ce_iv)

                strike_data['ce_iv'] = round(ce_iv * 100, 2)
                strike_data['ce_delta'] = round(ce_delta, 4)
                strike_data['ce_gamma'] = round(ce_gamma, 6)
                strike_data['ce_vega'] = round(ce_vega, 2)

            if pe_ltp > 0:
                pe_iv = GreeksCalculator.calculate_implied_volatility(spot, strike, T, pe_ltp, 'PE')
                pe_delta = GreeksCalculator.calculate_delta(spot, strike, T, pe_iv, 'PE')
                pe_gamma = GreeksCalculator.calculate_gamma(spot, strike, T, pe_iv)
                pe_vega = GreeksCalculator.calculate_vega(spot, strike, T, pe_iv)

                strike_data['pe_iv'] = round(pe_iv * 100, 2)
                strike_data['pe_delta'] = round(pe_delta, 4)
                strike_data['pe_gamma'] = round(pe_gamma, 6)
                strike_data['pe_vega'] = round(pe_vega, 2)

        return enriched_chain

    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        self.cache_timestamps.clear()
