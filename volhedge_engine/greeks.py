import math
from scipy.stats import norm
from scipy.optimize import brentq

class GreeksCalculator:
    """Black-Scholes Greeks Engine with Indian RBI risk-free rate (7.0%)"""

    RISK_FREE_RATE = 0.070  # 7.0% annual RBI rate

    @staticmethod
    def calculate_d1_d2(S, K, T, sigma):
        """Calculate d1 and d2 from Black-Scholes"""
        if T <= 0 or sigma <= 0:
            return None, None

        d1 = (math.log(S / K) + (GreeksCalculator.RISK_FREE_RATE + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        return d1, d2

    @staticmethod
    def calculate_call_price(S, K, T, sigma):
        """Call option price using Black-Scholes"""
        d1, d2 = GreeksCalculator.calculate_d1_d2(S, K, T, sigma)
        if d1 is None:
            return 0

        call = S * norm.cdf(d1) - K * math.exp(-GreeksCalculator.RISK_FREE_RATE * T) * norm.cdf(d2)
        return max(0, call)

    @staticmethod
    def calculate_put_price(S, K, T, sigma):
        """Put option price using Black-Scholes"""
        d1, d2 = GreeksCalculator.calculate_d1_d2(S, K, T, sigma)
        if d1 is None:
            return 0

        put = K * math.exp(-GreeksCalculator.RISK_FREE_RATE * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return max(0, put)

    @staticmethod
    def calculate_delta(S, K, T, sigma, opt_type='CE'):
        """Delta: rate of change of option price with spot"""
        d1, _ = GreeksCalculator.calculate_d1_d2(S, K, T, sigma)
        if d1 is None:
            return 0

        if opt_type == 'CE':
            return norm.cdf(d1)
        else:  # PE
            return norm.cdf(d1) - 1.0

    @staticmethod
    def calculate_gamma(S, K, T, sigma):
        """Gamma: rate of change of delta with spot"""
        d1, _ = GreeksCalculator.calculate_d1_d2(S, K, T, sigma)
        if d1 is None or T <= 0 or sigma <= 0:
            return 0

        return norm.pdf(d1) / (S * sigma * math.sqrt(T))

    @staticmethod
    def calculate_vega(S, K, T, sigma):
        """Vega: sensitivity to 1% change in volatility"""
        d1, _ = GreeksCalculator.calculate_d1_d2(S, K, T, sigma)
        if d1 is None or T <= 0 or sigma <= 0:
            return 0

        return S * math.sqrt(T) * norm.pdf(d1) / 100.0

    @staticmethod
    def calculate_theta(S, K, T, sigma, opt_type='CE'):
        """Theta: time decay per 1 calendar day"""
        d1, d2 = GreeksCalculator.calculate_d1_d2(S, K, T, sigma)
        if d1 is None or T <= 0 or sigma <= 0:
            return 0

        r = GreeksCalculator.RISK_FREE_RATE
        sqrt_T = math.sqrt(T)

        if opt_type == 'CE':
            theta = (-S * norm.pdf(d1) * sigma / (2 * sqrt_T) -
                    r * K * math.exp(-r * T) * norm.cdf(d2)) / 365.0
        else:  # PE
            theta = (-S * norm.pdf(d1) * sigma / (2 * sqrt_T) +
                    r * K * math.exp(-r * T) * norm.cdf(-d2)) / 365.0

        return theta

    @staticmethod
    def calculate_volga(S, K, T, sigma):
        """Volga: sensitivity to change in volatility (second-order vega)"""
        d1, d2 = GreeksCalculator.calculate_d1_d2(S, K, T, sigma)
        if d1 is None or T <= 0 or sigma <= 0:
            return 0

        sqrt_T = math.sqrt(T)
        volga = S * sqrt_T * norm.pdf(d1) * d1 * d2 / (sigma * 100.0)
        return volga

    @staticmethod
    def calculate_vanna(S, K, T, sigma, opt_type='CE'):
        """Vanna: sensitivity to changes in both delta and volatility"""
        d1, d2 = GreeksCalculator.calculate_d1_d2(S, K, T, sigma)
        if d1 is None or T <= 0 or sigma <= 0:
            return 0

        sqrt_T = math.sqrt(T)
        if opt_type == 'CE':
            vanna = -norm.pdf(d1) * d2 / sigma / 100.0
        else:  # PE
            vanna = -norm.pdf(d1) * d2 / sigma / 100.0

        return vanna

    @staticmethod
    def calculate_implied_volatility(S, K, T, market_price, opt_type='CE'):
        """Calculate IV using Brent root-finding solver"""

        def price_diff(sigma):
            if sigma <= 0:
                return float('inf')

            if opt_type == 'CE':
                theo_price = GreeksCalculator.calculate_call_price(S, K, T, sigma)
            else:
                theo_price = GreeksCalculator.calculate_put_price(S, K, T, sigma)

            return theo_price - market_price

        try:
            iv = brentq(price_diff, 0.001, 5.0, maxiter=100)
            return max(0.001, min(iv, 5.0))
        except ValueError:
            return 0

    @staticmethod
    def time_to_expiry_fraction(expiry_str, current_time=None):
        """Convert expiry string 'DD-MM-YYYY HH:MM:SS' to time fraction"""
        from datetime import datetime

        if current_time is None:
            current_time = datetime.now()

        try:
            expiry_parts = expiry_str.split()
            date_part = expiry_parts[0]
            time_part = expiry_parts[1] if len(expiry_parts) > 1 else "15:30:00"

            expiry = datetime.strptime(f"{date_part} {time_part}", "%d-%m-%Y %H:%M:%S")
            delta = expiry - current_time
            seconds_left = max(delta.total_seconds(), 1)
            return seconds_left / (365.0 * 86400)
        except:
            return 0.001
