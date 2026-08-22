import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from volhedge_engine.greeks import GreeksCalculator
from volhedge_engine.margin import MarginCalculator
from volhedge_engine.rebalancer import RebalancerEngine
from volhedge_engine.synthetic import SyntheticEngine


class PortfolioManager:
    """Multi-Tab Portfolio, Consolidation, & Greeks Recalculation"""

    def __init__(self, portfolio_file: str = "portfolio/saved_portfolio.json"):
        self.portfolio_file = portfolio_file
        self.portfolio = self.load_portfolio()

    def load_portfolio(self) -> Dict:
        """Load portfolio from JSON file"""
        if os.path.exists(self.portfolio_file):
            with open(self.portfolio_file, 'r') as f:
                return json.load(f)

        return {
            "positions": {
                "NIFTY": [],
                "BANKNIFTY": [],
                "FINNIFTY": [],
                "SILVERM": []
            },
            "lot_sizes": {
                "NIFTY": 75,
                "BANKNIFTY": 40,
                "FINNIFTY": 40,
                "SILVERM": 1
            },
            "spot_prices": {
                "NIFTY": 24252.0,
                "BANKNIFTY": 57761.95,
                "FINNIFTY": 26261.0,
                "SILVERM": 247855.0
            }
        }

    def save_portfolio(self):
        """Save portfolio to JSON file"""
        os.makedirs(os.path.dirname(self.portfolio_file), exist_ok=True)
        with open(self.portfolio_file, 'w') as f:
            json.dump(self.portfolio, f, indent=2)

    def add_position(self, symbol: str, position_data: Dict) -> bool:
        """Add or scale into position (consolidates by strike)"""
        if symbol not in self.portfolio["positions"]:
            self.portfolio["positions"][symbol] = []

        strike = position_data.get('strike')
        expiry = position_data.get('expiry')
        opt_type = position_data.get('opt_type')
        qty = position_data.get('qty')
        entry_price = position_data.get('entry_price')

        matching_pos = None
        for pos in self.portfolio["positions"][symbol]:
            if (pos.get('strike') == strike and
                pos.get('expiry') == expiry and
                pos.get('opt_type') == opt_type):
                matching_pos = pos
                break

        if matching_pos:
            old_qty = matching_pos.get('qty', 0)
            old_price = matching_pos.get('entry_price', 0)

            weighted_avg_price = (old_qty * old_price + qty * entry_price) / (old_qty + qty)

            matching_pos['qty'] = old_qty + qty
            matching_pos['entry_price'] = weighted_avg_price

            new_trade = {
                "id": f"t-{int(datetime.now().timestamp() * 1000)}",
                "date": datetime.now().strftime("%d-%m-%Y"),
                "time": datetime.now().strftime("%H:%M:%S"),
                "action": "BUY" if qty > 0 else "SELL",
                "qty": qty,
                "price": entry_price,
                "tag": position_data.get('tag', '')
            }
            if 'trades' not in matching_pos:
                matching_pos['trades'] = []
            matching_pos['trades'].append(new_trade)

        else:
            new_position = {
                "id": f"pos-{int(datetime.now().timestamp() * 1000)}",
                "symbol": symbol,
                "opt_type": opt_type,
                "strike": strike,
                "expiry": expiry,
                "qty": qty,
                "entry_price": entry_price,
                "current_price": entry_price,
                "tag": position_data.get('tag', ''),
                "trade_time": datetime.now().strftime("%H:%M:%S"),
                "trades": [{
                    "id": f"t-{int(datetime.now().timestamp() * 1000)}",
                    "date": datetime.now().strftime("%d-%m-%Y"),
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "action": "BUY" if qty > 0 else "SELL",
                    "qty": qty,
                    "price": entry_price,
                    "tag": position_data.get('tag', '')
                }],
                "iv": 0,
                "unit_delta": 0,
                "total_delta": 0,
                "unit_gamma": 0,
                "total_gamma": 0,
                "unit_vega": 0,
                "total_vega": 0,
                "unit_theta": 0,
                "total_theta": 0,
                "mtm": 0
            }
            self.portfolio["positions"][symbol].append(new_position)

        self.save_portfolio()
        return True

    def remove_position(self, symbol: str, pos_id: str) -> bool:
        """Remove position by ID"""
        if symbol in self.portfolio["positions"]:
            self.portfolio["positions"][symbol] = [
                p for p in self.portfolio["positions"][symbol]
                if p.get('id') != pos_id
            ]
            self.save_portfolio()
            return True
        return False

    def clear_positions(self, symbol: str) -> bool:
        """Clear all positions for a symbol"""
        if symbol in self.portfolio["positions"]:
            self.portfolio["positions"][symbol] = []
            self.save_portfolio()
            return True
        return False

    def add_tab(self, symbol: str) -> bool:
        """Add new scrip tab"""
        if symbol not in self.portfolio["positions"]:
            self.portfolio["positions"][symbol] = []
            self.portfolio["lot_sizes"][symbol] = 1
            self.portfolio["spot_prices"][symbol] = 0
            self.save_portfolio()
            return True
        return False

    def remove_tab(self, symbol: str) -> bool:
        """Remove scrip tab"""
        if symbol in self.portfolio["positions"]:
            del self.portfolio["positions"][symbol]
            if symbol in self.portfolio["lot_sizes"]:
                del self.portfolio["lot_sizes"][symbol]
            if symbol in self.portfolio["spot_prices"]:
                del self.portfolio["spot_prices"][symbol]
            self.save_portfolio()
            return True
        return False

    def update_prices(self, symbol: str, positions_with_prices: List[Dict]):
        """Update current prices and recalculate Greeks/Margins"""
        if symbol not in self.portfolio["positions"]:
            return

        for new_data in positions_with_prices:
            for pos in self.portfolio["positions"][symbol]:
                if pos.get('id') == new_data.get('id'):
                    current_price = new_data.get('current_price', pos.get('current_price'))
                    pos['current_price'] = current_price

                    mtm = (current_price - pos.get('entry_price', 0)) * pos.get('qty', 0)
                    pos['mtm'] = round(mtm, 2)

                    iv = new_data.get('iv', 0)
                    pos['iv'] = iv

                    spot = self.portfolio["spot_prices"].get(symbol, 0)
                    T = GreeksCalculator.time_to_expiry_fraction(pos.get('expiry', ''))

                    if T > 0 and iv > 0:
                        pos['unit_delta'] = round(GreeksCalculator.calculate_delta(
                            spot, pos.get('strike', 0), T, iv, pos.get('opt_type', 'CE')
                        ), 4)
                        pos['total_delta'] = round(pos['unit_delta'] * pos.get('qty', 0), 2)

                        pos['unit_gamma'] = round(GreeksCalculator.calculate_gamma(
                            spot, pos.get('strike', 0), T, iv
                        ), 6)
                        pos['total_gamma'] = round(pos['unit_gamma'] * pos.get('qty', 0), 2)

                        pos['unit_vega'] = round(GreeksCalculator.calculate_vega(
                            spot, pos.get('strike', 0), T, iv
                        ), 2)
                        pos['total_vega'] = round(pos['unit_vega'] * pos.get('qty', 0), 2)

                        pos['unit_theta'] = round(GreeksCalculator.calculate_theta(
                            spot, pos.get('strike', 0), T, iv, pos.get('opt_type', 'CE')
                        ), 4)
                        pos['total_theta'] = round(pos['unit_theta'] * pos.get('qty', 0), 2)

        self.save_portfolio()

    def get_portfolio_summary(self, symbol: str) -> Dict:
        """Get portfolio summary for symbol"""
        positions = self.portfolio["positions"].get(symbol, [])

        total_delta = sum(p.get('total_delta', 0) for p in positions)
        total_gamma = sum(p.get('total_gamma', 0) for p in positions)
        total_vega = sum(p.get('total_vega', 0) for p in positions)
        total_theta = sum(p.get('total_theta', 0) for p in positions)
        total_mtm = sum(p.get('mtm', 0) for p in positions)

        margin_info = MarginCalculator.calculate_portfolio_margin(
            {symbol: positions}, symbol
        )

        rebalance_info = RebalancerEngine.get_rebalance_recommendation(symbol, positions)

        return {
            'symbol': symbol,
            'positions_count': len(positions),
            'total_delta': round(total_delta, 2),
            'total_gamma': round(total_gamma, 4),
            'total_vega': round(total_vega, 2),
            'total_theta': round(total_theta, 2),
            'gross_mtm': round(total_mtm, 2),
            'span_margin': round(margin_info['span'], 2),
            'exposure_margin': round(margin_info['exposure'], 2),
            'total_margin': round(margin_info['total'], 2),
            'rebalance_needed': rebalance_info['rebalance_needed'],
            'rebalance_recommendation': rebalance_info['recommendation']
        }

    def get_all_tabs(self) -> List[str]:
        """Get all active tabs"""
        return list(self.portfolio["positions"].keys())

    def get_positions(self, symbol: str) -> List[Dict]:
        """Get all positions for symbol"""
        return self.portfolio["positions"].get(symbol, [])

    def update_spot_price(self, symbol: str, spot_price: float):
        """Update spot price for symbol"""
        if symbol in self.portfolio["spot_prices"]:
            self.portfolio["spot_prices"][symbol] = spot_price
            self.save_portfolio()

    def get_spot_price(self, symbol: str) -> float:
        """Get current spot price"""
        return self.portfolio["spot_prices"].get(symbol, 0)

    def get_lot_size(self, symbol: str) -> int:
        """Get lot size for symbol"""
        return self.portfolio["lot_sizes"].get(symbol, 1)
