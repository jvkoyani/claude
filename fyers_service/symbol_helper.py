class SymbolHelper:
    """Symbol Format Resolver for NSE, BSE, MCX"""

    EXPIRY_DATES = {
        'NIFTY': 'NSE:NIFTY26AUG24',
        'BANKNIFTY': 'NSE:BANKNIFTY26AUG24',
        'FINNIFTY': 'NSE:FINNIFTY26AUG24',
        'SENSEX': 'BSE:SENSEX26AUG24',
        'CRUDEOIL': 'MCX:CRUDEOIL26NOV',
        'GOLD': 'MCX:GOLD26NOV',
        'SILVERM': 'MCX:SILVERM26NOV',
    }

    INSTRUMENT_TYPES = {
        'CE': 'CE',
        'PE': 'PE',
        'FUT': 'FUT',
    }

    @staticmethod
    def format_option_symbol(base_symbol: str, strike: float, expiry: str, opt_type: str):
        """
        Format option symbol for Fyers:
        NSE:NIFTY26AUG24200CE
        MCX:SILVERM26NOVFUT
        """
        base_symbol = base_symbol.upper()

        if opt_type.upper() in ['CE', 'PE']:
            strike_str = str(int(strike))
            symbol = f"{base_symbol}{expiry.replace('-', '')}{strike_str}{opt_type.upper()}"
        else:
            symbol = f"{base_symbol}{expiry.replace('-', '')}{opt_type.upper()}"

        return symbol

    @staticmethod
    def format_future_symbol(base_symbol: str, expiry: str):
        """
        Format future symbol for Fyers:
        NSE:NIFTY26AUG24FUT
        """
        base_symbol = base_symbol.upper()
        expiry_clean = expiry.replace('-', '')
        return f"{base_symbol}{expiry_clean}FUT"

    @staticmethod
    def parse_fyers_symbol(fyers_symbol: str):
        """
        Parse Fyers symbol and extract components:
        NSE:NIFTY26AUG24200CE -> {'exchange': 'NSE', 'symbol': 'NIFTY', 'expiry': '26AUG24', 'strike': 200, 'type': 'CE'}
        """
        try:
            if ':' in fyers_symbol:
                exchange, symbol_part = fyers_symbol.split(':')
            else:
                exchange = 'NSE'
                symbol_part = fyers_symbol

            result = {
                'exchange': exchange,
                'symbol': '',
                'expiry': '',
                'strike': 0,
                'type': '',
                'raw': fyers_symbol
            }

            type_suffix = symbol_part[-2:]
            if type_suffix in ['CE', 'PE']:
                result['type'] = type_suffix
                symbol_part = symbol_part[:-2]
            elif 'FUT' in symbol_part:
                result['type'] = 'FUT'
                symbol_part = symbol_part.replace('FUT', '')

            for base in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX', 'CRUDEOIL', 'GOLD', 'SILVERM']:
                if symbol_part.startswith(base):
                    result['symbol'] = base
                    rest = symbol_part[len(base):]

                    if result['type'] in ['CE', 'PE']:
                        if rest[-3:].isdigit():
                            result['strike'] = float(rest[-3:])
                            result['expiry'] = rest[:-3]
                        else:
                            result['expiry'] = rest
                    else:
                        result['expiry'] = rest

                    break

            return result
        except:
            return {'raw': fyers_symbol}

    @staticmethod
    def get_exchange_prefix(symbol: str):
        """Get exchange prefix for symbol"""
        symbol = symbol.upper()

        if any(x in symbol for x in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX']):
            if 'SENSEX' in symbol:
                return 'BSE'
            return 'NSE'
        elif any(x in symbol for x in ['GOLD', 'SILVER', 'CRUDE', 'CRUDEOIL']):
            return 'MCX'
        else:
            return 'NSE'

    @staticmethod
    def add_exchange_prefix(symbol: str):
        """Add exchange prefix if not present"""
        if ':' in symbol:
            return symbol

        prefix = SymbolHelper.get_exchange_prefix(symbol)
        return f"{prefix}:{symbol}"

    @staticmethod
    def remove_exchange_prefix(symbol: str):
        """Remove exchange prefix"""
        if ':' in symbol:
            return symbol.split(':')[1]
        return symbol

    @staticmethod
    def get_closest_strike(spot: float, available_strikes: list, atm_offset: int = 0):
        """Get closest strike to spot (ATM)"""
        if not available_strikes:
            return spot

        if atm_offset == 0:
            return min(available_strikes, key=lambda x: abs(x - spot))

        closest = min(available_strikes, key=lambda x: abs(x - spot))
        idx = available_strikes.index(closest)

        if atm_offset > 0 and idx + atm_offset < len(available_strikes):
            return available_strikes[idx + atm_offset]
        elif atm_offset < 0 and idx + atm_offset >= 0:
            return available_strikes[idx + atm_offset]

        return closest
