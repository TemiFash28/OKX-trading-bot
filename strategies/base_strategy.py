from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def generate_signal(self, market_data: dict) -> tuple:
        """
        Return (action: 'buy' | 'sell' | None, price)
        """
        pass

    def update_state(self, filled_order):
        pass
