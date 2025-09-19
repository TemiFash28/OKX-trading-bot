import pandas as pd
import ta
from strategies.base_strategy import BaseStrategy

class RSIStrategy(BaseStrategy):
    def generate_signal(self, market_data):
        try:
            df = pd.DataFrame(market_data['1h'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()

            trend_df = pd.DataFrame(market_data['4h'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            trend_sma = ta.trend.SMAIndicator(trend_df['close'], window=20).sma_indicator()
            uptrend = trend_df['close'].iloc[-1] > trend_sma.iloc[-1]

            rsi = df['rsi'].iloc[-1]
            price = df['close'].iloc[-1]

            if rsi < 30 and uptrend:
                return 'buy', price * 0.99
            elif rsi > 70:
                return 'sell', price * 1.01
            return None, None

        except Exception as e:
            print(f"RSI strategy error: {e}")
            return None, None
