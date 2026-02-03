# 📈 IDX Quant Sentiment Tools

Python-based research toolkit to extract historical price data (OHLCV) and analyze crowd-sourced market sentiment from Indonesian investment platforms.

## 🚀 Features

* **Price Scraper:** Fetches daily OHLCV (Open, High, Low, Close, Volume) data for any IDX stock ticker.
* **Smart Sentiment Analysis:**
    * Scrapes real-time user discussions (Stream).
    * **Dual-Signal Detection:** Captures sentiment not just from mood labels ('Bullish'/'Bearish') but also from quantitative **Price Targets** set by users.
    * **Anti-Masking:** Retrieves original content text (avoids masked/hidden ticker symbols).
* **Clean Output:** Automatically saves data to CSV format for further analysis in Python/Excel.

## 🛠️ Tech Stack
* **Python 3.14.2**
* **Pandas** (Data Manipulation)
* **Requests** (API Handling)
* **Python-Dotenv** (Security & Config)

## ⚙️ Configuration
To run this tool, you need to set up your environment variables in '.env'
1.  Authentication Token and the target API endpoint is required for this.
2.  Copy and paste the following code into your `.env` file:

# Authentication Token
# Get this from your target platform's request headers (Authorization: Bearer ...)
TARGET_AUTH_TOKEN="Bearer ..."

# Target API Endpoints
# Replace with the specific API endpoints of the platform you are researching
TARGET_PRICE_URL="..."
TARGET_STREAM_URL="..."

## ⚠️ Disclaimer
This project is for educational and research purposes only.
