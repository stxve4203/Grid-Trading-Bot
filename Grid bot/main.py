from binance.client import Client
import pandas as pd
from classes import Bot
from threading import Thread

# Usage example
api_key = ''
api_secret = ''
client = Client(api_key, api_secret, testnet=True)

bot = Bot(client=client,
          n=10,
          symbol='BTCUSDT',
          volume=0.1,
          profit_target=5,
          proportion=0.1)

bot.run()


