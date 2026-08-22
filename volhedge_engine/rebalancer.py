class RebalancerEngine:
    """Delta Neutral Rebalancing Recommendation Engine"""

    LOT_SIZES = {
        'NIFTY': 75,
        'BANKNIFTY': 40,
        'FINNIFTY': 40,
        'SENSEX': 10,
        'CRUDEOIL': 100,
        'GOLD': 100,
        'SILVERM': 1,
        'RELIANCE': 1,
        'TCS': 1,
    }

    @staticmethod
    def get_lot_size(symbol):
        """Get lot size for symbol"""
        symbol_upper = symbol.upper()
        if symbol_upper in RebalancerEngine.LOT_SIZES:
            return RebalancerEngine.LOT_SIZES[symbol_upper]

        for key in RebalancerEngine.LOT_SIZES:
            if key in symbol_upper:
                return RebalancerEngine.LOT_SIZES[key]

        return 1

    @staticmethod
    def calculate_net_delta(positions):
        """
        Calculate total portfolio delta:
        Net Delta = Sum(Unit Delta × Quantity)
        """
        net_delta = 0
        for pos in positions:
            unit_delta = pos.get('unit_delta', 0)
            qty = pos.get('qty', 0)
            net_delta += unit_delta * qty

        return net_delta

    @staticmethod
    def calculate_rebalance_qty(symbol, net_delta_imbalance):
        """
        Calculate future contract quantity to rebalance portfolio:
        Required Future Rebalance Qty = round(-Net Delta Imbalance / Lot Size) × Lot Size
        """
        lot_size = RebalancerEngine.get_lot_size(symbol)

        if lot_size == 0:
            return 0

        required_qty = -net_delta_imbalance / lot_size
        rounded_qty = round(required_qty) * lot_size

        return int(rounded_qty)

    @staticmethod
    def get_rebalance_recommendation(symbol, positions, tolerance=0.05):
        """
        Get rebalancing recommendation:
        - If net delta falls outside tolerance band (±5%), recommend futures position
        """
        net_delta = RebalancerEngine.calculate_net_delta(positions)
        lot_size = RebalancerEngine.get_lot_size(symbol)

        if abs(net_delta) < lot_size * tolerance:
            return {
                'rebalance_needed': False,
                'net_delta': net_delta,
                'recommendation': 'Portfolio is delta-neutral',
                'action': None,
                'quantity': 0
            }

        rebalance_qty = RebalancerEngine.calculate_rebalance_qty(symbol, net_delta)

        action = 'BUY' if rebalance_qty > 0 else 'SELL'
        quantity = abs(rebalance_qty)

        return {
            'rebalance_needed': True,
            'net_delta': net_delta,
            'recommendation': f'{action} {quantity} qty {symbol} Future',
            'action': action,
            'quantity': quantity
        }

    @staticmethod
    def delta_neutral_strike_selection(spot, strikes):
        """
        Find ATM strike for delta-neutral strategy
        Recommended strike is closest to spot price
        """
        if not strikes:
            return spot

        atm_strike = min(strikes, key=lambda x: abs(x - spot))
        return atm_strike

    @staticmethod
    def calculate_hedge_ratio(net_delta, option_delta):
        """
        Calculate how many option contracts needed to hedge N futures
        Hedge Qty = Net Delta / Option Delta (in absolute value)
        """
        if option_delta == 0:
            return 0

        hedge_qty = abs(net_delta / option_delta)
        return hedge_qty

    @staticmethod
    def calculate_delta_range(positions, symbol):
        """Calculate delta range (min-max) across all positions"""
        if not positions:
            return 0, 0

        deltas = [pos.get('unit_delta', 0) for pos in positions]
        return min(deltas), max(deltas)

    @staticmethod
    def get_delta_neutral_bands(symbol):
        """Get recommended delta-neutral tolerance bands (±5% of lot size)"""
        lot_size = RebalancerEngine.get_lot_size(symbol)
        lower_band = -lot_size * 0.05
        upper_band = lot_size * 0.05
        return lower_band, upper_band

    @staticmethod
    def calculate_gamma_exposure(positions):
        """Calculate total gamma exposure (convexity risk)"""
        total_gamma = 0
        for pos in positions:
            unit_gamma = pos.get('unit_gamma', 0)
            qty = pos.get('qty', 0)
            total_gamma += unit_gamma * qty

        return total_gamma
