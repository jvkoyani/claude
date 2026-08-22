class SyntheticEngine:
    """Synthetic Future & Put-Call Parity Calculator"""

    @staticmethod
    def calculate_synthetic_future(atm_strike, atm_call_ltp, atm_put_ltp):
        """
        Calculate Synthetic Future using:
        Syn Future = ATM Strike + (ATM Call LTP - ATM Put LTP)
        """
        if atm_call_ltp is None or atm_put_ltp is None:
            return atm_strike

        syn_future = atm_strike + (atm_call_ltp - atm_put_ltp)
        return syn_future

    @staticmethod
    def calculate_fair_call_price(spot, strike, put_price, rate=0.070, time_to_expiry=0):
        """
        Put-Call Parity: C = P + S - K*e^(-r*T)
        Fair Call = Put Price + Spot - Discounted Strike
        """
        import math
        discount_factor = math.exp(-rate * time_to_expiry)
        fair_call = put_price + spot - strike * discount_factor
        return max(0, fair_call)

    @staticmethod
    def calculate_fair_put_price(spot, strike, call_price, rate=0.070, time_to_expiry=0):
        """
        Put-Call Parity: P = C - S + K*e^(-r*T)
        Fair Put = Call Price - Spot + Discounted Strike
        """
        import math
        discount_factor = math.exp(-rate * time_to_expiry)
        fair_put = call_price - spot + strike * discount_factor
        return max(0, fair_put)

    @staticmethod
    def find_atm_strike(spot, strikes):
        """Find the closest ATM (At-The-Money) strike from list"""
        if not strikes:
            return spot

        return min(strikes, key=lambda x: abs(x - spot))

    @staticmethod
    def calculate_intrinsic_value(spot, strike, opt_type='CE'):
        """Calculate intrinsic value of option"""
        if opt_type == 'CE':
            return max(spot - strike, 0)
        else:  # PE
            return max(strike - spot, 0)

    @staticmethod
    def calculate_time_value(option_price, intrinsic_value):
        """Time Value = Option Price - Intrinsic Value"""
        return max(option_price - intrinsic_value, 0)
