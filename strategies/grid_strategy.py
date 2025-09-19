from strategies.base_strategy import BaseStrategy

class GridStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        self.base_price = None

    def generate_signal(self, market_data):
        try:
            df = market_data['1h']
            current_price = df[-1][4]  # last close

            grid_size = self.config.get('base_grid_size', 1.5)
            if self.base_price is None:
                self.base_price = current_price

            upper = self.base_price * (1 + grid_size / 100)
            lower = self.base_price * (1 - grid_size / 100)

            if current_price <= lower:
                self.base_price = current_price
                return 'buy', current_price
            elif current_price >= upper:
                self.base_price = current_price
                return 'sell', current_price
            return None, None

        except Exception as e:
            print(f"Grid strategy error: {e}")
            return None, None
