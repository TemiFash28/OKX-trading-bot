# OKX Trading Bot

A Python-based automated trading bot for the **OKX exchange**, built on [ccxt](https://github.com/ccxt/ccxt).  
The bot supports custom strategy plugins, dry-run/live trading modes, daily risk management, and detailed trade logging.

---

## 🚀 Features
- ✅ Connects to OKX via `ccxt`
- ✅ Strategy plugin support (`rsi` included, extendable)
- ✅ Dry-run mode for safe testing
- ✅ Live trading mode with API keys
- ✅ Trade logging (CSV + console logs)
- ✅ Daily limits: max trades & max spend
- ✅ Automatic reset of daily counters
- ✅ Configurable via `config.json` + `.env`

---

## 📂 Project Structure
```
.
├── okx_bot.py        # Main bot script
├── config.json       # Bot configuration (pair, strategy, risk settings)
├── requirements.txt  # Python dependencies
├── .env              # Your OKX API keys (not in repo, create manually)
└── strategies (your strategies module, add as needed)
```

---

## ⚙️ Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/okx-bot.git
   cd okx-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env` file**  
   Add your OKX API credentials:
   ```env
   OKX_API_KEY=your_api_key
   OKX_API_SECRET=your_api_secret
   OKX_API_PASSPHRASE=your_passphrase
   ```

4. **Configure `config.json`**  
   Example:
   ```json
   {
     "pair": "ETH/USDT",
     "strategy": "rsi",
     "base_dca_amount": 0.01,
     "base_grid_size": 1.5,
     "dca_dip_threshold": 3,
     "peak_hours": [8, 17],
     "low_liquidity_hours": [4, 6],
     "live_trading": false,
     "max_daily_spend": 30,
     "max_trades_per_day": 5
   }
   ```

   - Set `"live_trading": false` to run in **dry-run mode** (no real trades).  
   - Switch to `true` when ready to go live.

---

## ▶️ Usage

Run the bot:
```bash
python okx_bot.py
```

Logs are saved to:
- `bot.log` – runtime logs
- `hmrc_log.csv` – trade history

---

## 🛠️ Extending Strategies
Strategies are loaded via the `strategies` module.  
To add a new one:
1. Implement a new strategy class with `generate_signal(market_data)`.
2. Reference it in `config.json`.

---

## ⚠️ Disclaimer
This bot is provided **for educational purposes only**.  
Use at your own risk. Cryptocurrency trading involves significant risk of loss.

---

## 📜 License
MIT
