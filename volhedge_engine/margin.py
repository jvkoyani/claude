class MarginCalculator:
    """SEBI/NSE SPAN + Exposure Margin Engine"""

    MARGIN_RATES = {
        'NIFTY': {'span': 0.0825, 'exposure': 0.020},
        'BANKNIFTY': {'span': 0.0825, 'exposure': 0.020},
        'FINNIFTY': {'span': 0.0825, 'exposure': 0.020},
        'SENSEX': {'span': 0.0825, 'exposure': 0.020},
        'CRUDEOIL': {'span': 0.115, 'exposure': 0.0125},
        'GOLD': {'span': 0.115, 'exposure': 0.0125},
        'SILVERM': {'span': 0.115, 'exposure': 0.0125},
        'RELIANCE': {'span': 0.135, 'exposure': 0.035},
        'TCS': {'span': 0.135, 'exposure': 0.035},
    }

    @staticmethod
    def get_margin_rates(symbol):
        """Get SPAN and Exposure margin rates for symbol"""
        symbol_upper = symbol.upper()
        if symbol_upper in MarginCalculator.MARGIN_RATES:
            return MarginCalculator.MARGIN_RATES[symbol_upper]

        for key in MarginCalculator.MARGIN_RATES:
            if key in symbol_upper:
                return MarginCalculator.MARGIN_RATES[key]

        return {'span': 0.10, 'exposure': 0.025}

    @staticmethod
    def calculate_naked_margin(symbol, price, qty, opt_type='CE'):
        """Calculate naked option margin (for short positions)"""
        rates = MarginCalculator.get_margin_rates(symbol)
        span_margin = price * qty * rates['span']
        exposure_margin = price * qty * rates['exposure']
        total_margin = span_margin + exposure_margin
        return {
            'span': span_margin,
            'exposure': exposure_margin,
            'total': total_margin
        }

    @staticmethod
    def calculate_strangle_margin(symbol, call_price, put_price, qty):
        """
        Calculate margin for Short Strangle:
        Pairs × (1.18 × Naked Lot Margin)
        """
        rates = MarginCalculator.get_margin_rates(symbol)

        max_price = max(call_price, put_price)
        naked_margin = max_price * qty * (rates['span'] + rates['exposure'])
        strangle_margin = qty * 1.18 * naked_margin

        return {
            'span': strangle_margin * 0.8,
            'exposure': strangle_margin * 0.2,
            'total': strangle_margin
        }

    @staticmethod
    def calculate_vertical_spread_margin(symbol, long_price, short_price, qty):
        """
        Calculate margin for Vertical Spreads:
        75% SPAN relief (25% margin required)
        """
        rates = MarginCalculator.get_margin_rates(symbol)
        max_price = max(long_price, short_price)
        naked_margin = max_price * qty * (rates['span'] + rates['exposure'])

        spread_margin = naked_margin * 0.25

        return {
            'span': spread_margin * 0.8,
            'exposure': spread_margin * 0.2,
            'total': spread_margin
        }

    @staticmethod
    def calculate_long_option_margin(symbol, price, qty):
        """Long options require premium only, zero margin"""
        return {
            'span': 0,
            'exposure': 0,
            'total': 0
        }

    @staticmethod
    def calculate_position_margin(symbol, position_type, price, qty, additional_info=None):
        """
        Calculate margin for different position types:
        - NAKED_SHORT: Naked short put/call
        - STRANGLE: Short strangle/straddle
        - VERTICAL_SPREAD: Bull call/put spread
        - LONG: Long option (zero margin)
        """
        if position_type == 'LONG':
            return MarginCalculator.calculate_long_option_margin(symbol, price, qty)
        elif position_type == 'NAKED_SHORT':
            return MarginCalculator.calculate_naked_margin(symbol, price, abs(qty))
        elif position_type == 'STRANGLE':
            if additional_info and 'pair_price' in additional_info:
                return MarginCalculator.calculate_strangle_margin(
                    symbol, price, additional_info['pair_price'], abs(qty)
                )
            return MarginCalculator.calculate_naked_margin(symbol, price, abs(qty))
        elif position_type == 'VERTICAL_SPREAD':
            if additional_info and 'pair_price' in additional_info:
                return MarginCalculator.calculate_vertical_spread_margin(
                    symbol, price, additional_info['pair_price'], abs(qty)
                )
            return MarginCalculator.calculate_naked_margin(symbol, price, abs(qty))
        else:
            return MarginCalculator.calculate_naked_margin(symbol, price, abs(qty))

    @staticmethod
    def calculate_portfolio_margin(positions, symbol):
        """Calculate total margin for all positions in a symbol"""
        total_span = 0
        total_exposure = 0

        for pos in positions.get(symbol, []):
            margin = MarginCalculator.calculate_naked_margin(
                symbol, pos.get('current_price', 0), abs(pos.get('qty', 0))
            )
            total_span += margin['span']
            total_exposure += margin['exposure']

        return {
            'span': total_span,
            'exposure': total_exposure,
            'total': total_span + total_exposure
        }
