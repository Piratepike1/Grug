# twitter_crypto_bot.py
```python
import os
import logging
import tweepy
import requests
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

# Load environment variables from .env file
load_dotenv()

# Twitter API credentials
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Coin info
COIN_NAME = os.getenv('COIN_NAME', 'Rug')
COIN_TICKER = os.getenv('COIN_TICKER', 'GRUG')
COIN_CONTRACT = os.getenv('COIN_CONTRACT')  # e.g. EuDGugoPdQ3E8T8ENxG2xSQdF8Cm3CTy16RSSVoFpump

# CoinGecko API
CG_API_URL = "https://api.coingecko.com/api/v3/simple/token_price/ethereum"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger()

# Authenticate with Twitter API v1.1 for mentions
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# Twitter v2 client for posting
token_client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET,
    wait_on_rate_limit=True
)

# File to store last mention ID
LAST_ID_FILE = 'last_mention_id.txt'

def read_last_id():
    try:
        with open(LAST_ID_FILE, 'r') as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return None


def write_last_id(last_id):
    with open(LAST_ID_FILE, 'w') as f:
        f.write(str(last_id))


def reply_to_mentions():
    last_id = read_last_id()
    mentions = api.mentions_timeline(since_id=last_id, tweet_mode='extended')
    for mention in reversed(mentions):
        try:
            text = (f"Hey @{mention.user.screen_name}, thanks for the mention! {COIN_NAME} (${COIN_TICKER}) is live."
                    f" Check it out: https://etherscan.io/token/{COIN_CONTRACT} 🚀")
            api.update_status(status=text, in_reply_to_status_id=mention.id)
            write_last_id(mention.id)
            logger.info(f"Replied to @{mention.user.screen_name} ({mention.id})")
        except Exception as e:
            logger.error(f"Error replying: {e}")


def get_current_price():
    params = {'contract_addresses': COIN_CONTRACT, 'vs_currencies': 'usd'}
    data = requests.get(CG_API_URL, params=params).json()
    return data.get(COIN_CONTRACT.lower(), {}).get('usd', 0.0)


def post_scheduled_tweet():
    price = get_current_price()
    tweet = (f"🔔 {COIN_NAME} (${COIN_TICKER}) current price: ${price:.6f} USD." \
             f" Etherscan: https://etherscan.io/token/{COIN_CONTRACT} #crypto #DeFi")
    token_client.create_tweet(text=tweet)
    logger.info("Scheduled tweet posted.")


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(reply_to_mentions, 'interval', minutes=1)
    scheduler.add_job(post_scheduled_tweet, 'interval', hours=6)
    logger.info("Starting Rug ($GRUG) Twitter bot...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Twitter bot shutting down.")
```

---

# Dockerfile
```Dockerfile
# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy project files
COPY . /app/

# Command to run on container start
CMD ["python", "twitter_crypto_bot.py"]
```

# requirements.txt
```
tweepy
python-dotenv
apscheduler
requests
```

---

# docker-compose.yml
```yaml
version: "3.8"
services:
  twitter-bot:
    build: .
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./last_mention_id.txt:/app/last_mention_id.txt
