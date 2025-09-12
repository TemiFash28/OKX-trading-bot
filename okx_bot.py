# okx_bot.py (updated version integrating strategy plugins + balance caching + lower threshold)
import os
import time
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import ccxt
import logging
from logging.handlers import RotatingFileHandler
import sys
import signal

from strategy_loader import load_strategy

CONFIG_FILE = 'config.json'
LOG_FILE = 'hmrc_log.csv'
MAX_LOG_SIZE = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 3

MIN_TRADE_THRESHOLD = 1.0  # lowered from $5 to $1 for testing

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler('bot.log', maxBytes=MAX_LOG_SIZE, backupCount=LOG_BACKUP_COUNT),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        required_fields = ['pair', 'strategy']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required config field: {field}")
        return config
    except Exception as e:
        logger.error(f"Config loading failed: {e}")
        raise

class GracefulExiter:
    def __init__(self):
        self.state = False
        signal.signal(signal.SIGINT, self.change_state)
        signal.signal(signal.SIGTERM, self.change_state)
    def change_state(self, signum, frame):
        logger.info("Received shutdown signal")
        self.state = True
    def exit(self):
        return self.state

class TradeLogger:
    def __init__(self, filename=LOG_FILE):
        self.filename = filename
        self._initialize_file()

    def _initialize_file(self):
        try:
            if not os.path.exists(self.filename):
                with open(self.filename, 'w') as f:
                    f.write("timestamp,action,amount,price,notes\n")
        except Exception as e:
            logger.error(f"Failed to initialize trade log: {e}")

    def log_trade(self, action, amount, price, notes=""):
        try:
            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()},{action},{amount},{price},{notes}\n")
            logger.info(f"Logged trade: {action} {amount} @ {price}")
        except Exception as e:
            logger.error(f"Trade logging failed: {e}")

class TradingBot:
    def __init__(self):
        load_dotenv()
        self.config = load_config()
        self.exchange = ccxt.okx({
            'apiKey': os.getenv('OKX_API_KEY', ''),
            'secret': os.getenv('OKX_API_SECRET', ''),
            'password': os.getenv('OKX_API_PASSPHRASE', ''),
            'enableRateLimit': True,
            'timeout': 30000,
            'options': {
                'defaultType': 'spot',
                'adjustForTimeDifference': True
            }
        })
        self.strategy = load_strategy(self.config['strategy'], self.config)
        self.trade_logger = TradeLogger()
        self.exit_flag = GracefulExiter()
        self.daily_trade_count = 0
        self.daily_spent = 0.0
        self.current_day = datetime.now().date()

    def reset_daily_limits_if_needed(self):
        now = datetime.now().date()
        if now != self.current_day:
            self.current_day = now
            self.daily_trade_count = 0
            self.daily_spent = 0.0
            logger.info("Daily limits reset.")

    def get_trade_amount(self, price, usdt):
        amount_usdt = usdt * 0.05
        if amount_usdt < MIN_TRADE_THRESHOLD:
            logger.warning(f"Trade skipped: amount below minimum trade threshold (${MIN_TRADE_THRESHOLD})")
            return 0
        return round(amount_usdt / price, 6)

    def check_daily_limits(self, trade_type, cost_usdt):
        max_trades = self.config.get("max_trades_per_day", 5)
        max_spend = self.config.get("max_daily_spend", 30)
        if trade_type == 'buy':
            if self.daily_trade_count >= max_trades:
                logger.warning("Trade skipped: daily trade count exceeded")
                return False
            if self.daily_spent + cost_usdt > max_spend:
                logger.warning("Trade skipped: daily spend limit exceeded")
                return False
        return True

    def execute_trade(self, action, price, amount, usdt):
        try:
            pair = self.config['pair']
            live = self.config.get("live_trading", False)
            usdt_cost = amount * price

            if action == 'buy':
                if usdt < usdt_cost:
                    logger.warning("Trade skipped: not enough USDT for buy")
                    return False
                if not self.check_daily_limits(action, usdt_cost):
                    return False

            if not live:
                logger.info(f"[DRY-RUN] Would {action} {amount} {pair} at {price}")
                self.trade_logger.log_trade(action, amount, price, "dry_run")
                return True

            order = None
            if action == 'buy':
                order = self.exchange.create_market_buy_order(pair, amount)
                self.daily_spent += usdt_cost
                self.daily_trade_count += 1
            elif action == 'sell':
                order = self.exchange.create_market_sell_order(pair, amount)

            self.trade_logger.log_trade(action, amount, price, f"Live order ID: {order['id'] if order else 'N/A'}")
            logger.info(f"Executed {action} order: {order}")
            return True

        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            return False

    def run(self):
        logger.info("Starting Trading Bot (Live Mode)" if self.config.get("live_trading", False) else "Starting Trading Bot (Dry-Run Mode)")
        while not self.exit_flag.exit():
            try:
                self.reset_daily_limits_if_needed()
                balance = self.exchange.fetch_balance()
                usdt = balance['total'].get('USDT', 0)

                market_data = {
                    '1h': self.exchange.fetch_ohlcv(self.config['pair'], '1h', limit=100),
                    '4h': self.exchange.fetch_ohlcv(self.config['pair'], '4h', limit=100)
                }

                action, target_price = self.strategy.generate_signal(market_data)
                if action and target_price:
                    amount = self.get_trade_amount(target_price, usdt)
                    if amount > 0:
                        self.execute_trade(action, target_price, amount, usdt)

                time.sleep(60)

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(300)

        logger.info("Shutting down bot gracefully")

if __name__ == "__main__":
    try:
        bot = TradingBot()
        bot.run()
    except Exception as e:
        logger.critical(f"Critical failure: {e}")
        sys.exit(1)
