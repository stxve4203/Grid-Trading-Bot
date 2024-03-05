import MetaTrader5 as mt5
import pandas as pd
from binance.client import Client
from binance.enums import *
import time

class Bot:
    def __init__(self, client, n, symbol, volume, profit_target, proportion):
        self.client = client
        self.n = n
        self.symbol = symbol
        self.volume = volume
        self.profit_target = profit_target
        self.proportion = proportion

    def buy_limit(self, symbol, volume, price):
        request = self.client.order_limit_buy(
            symbol=symbol,
            price=price,
            type_time=TIME_IN_FORCE_GTC
        )

        print(request)

    def sell_limit(self, symbol, volume, price):
        request = self.client.order_limit_sell(
            symbol=symbol,
            price=price,
            timeInForce=TIME_IN_FORCE_GTC
        )

        print(request)

    def cal_profit(self, symbol):
        usd_positions = self.client.get_my_trades(symbol=symbol)
        df = pd.DataFrame(list(usd_positions), columns=usd_positions[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.drop(['time_update', 'time_msc', 'time_update_msc', 'external_id'], axis=1, inplace=True)
        profit = float(df["profit"].sum())
        return profit

    def cal_volume(self, symbol):
        usd_positions = self.client.get_my_trades(symbol=symbol)
        df = pd.DataFrame(list(usd_positions), columns=usd_positions[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.drop(['time_update', 'time_msc', 'time_update_msc', 'external_id'], axis=1, inplace=True)
        profit = float(df["volume"].sum())
        return profit

    def cal_buy_profit(self, symbol):
        usd_positions = self.client.get_my_trades(symbol=symbol)
        df = pd.DataFrame(list(usd_positions), columns=usd_positions[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.drop(['time_update', 'time_msc', 'time_update_msc', 'external_id'], axis=1, inplace=True)
        df = df.loc[df.type == 0]
        profit = float(df["profit"].sum())
        return profit

    def cal_sell_profit(self, symbol):
        usd_positions = self.client.get_my_trades(symbol=symbol)
        df = pd.DataFrame(list(usd_positions), columns=usd_positions[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.drop(['time_update', 'time_msc', 'time_update_msc', 'external_id'], axis=1, inplace=True)
        df = df.loc[df.type == 1]
        profit = float(df["profit"].sum())
        return profit

    def cal_buy_margin(self, symbol):
        usd_positions = self.client.get_my_trades(symbol=symbol)
        df = pd.DataFrame(list(usd_positions), columns=usd_positions[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.drop(['time_update', 'time_msc', 'time_update_msc', 'external_id'], axis=1, inplace=True)
        df = df.loc[df.type == 0]

        sum = 0
        for i in df.index:
            volume = df.volume[i]
            open_price = df.price_open[i]
            margin = self.client.get_all_margin_orders(symbol=symbol, limit=20)
            sum += margin
        return sum

    def cal_sell_margin(self, symbol):
        usd_positions = mt5.positions_get(symbol=symbol)
        df = pd.DataFrame(list(usd_positions), columns=usd_positions[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.drop(['time_update', 'time_msc', 'time_update_msc', 'external_id'], axis=1, inplace=True)
        df = df.loc[df.type == 1]

        sum = 0
        for i in df.index:
            volume = df.volume[i]
            open_price = df.price_open[i]
            margin = self.client.get_all_margin_orders(symbol=symbol, limit=20)
            sum += margin
        return sum

    def cal_pct_buy_profit(self, symbol):
        profit = self.cal_buy_profit(symbol)
        margin = self.cal_buy_margin(symbol)
        pct = (profit / margin) * 100
        return pct

    def cal_pct_sell_profit(self, symbol):
        profit = self.cal_sell_profit(symbol)
        margin = self.cal_sell_margin(symbol)
        pct = (profit / margin) * 100
        return pct

    def close_position(self, position):
        # Get the latest ticker price for the symbol
        ticker = self.client.get_symbol_ticker(symbol=position['symbol'])
        latest_price = float(ticker['price'])

        # Determine the order side based on the position type
        order_side = Client.SIDE_SELL if position['side'] == 'BUY' else Client.SIDE_BUY

        # Create a market order to close the position
        order = self.client.create_order(
            symbol=position['symbol'],
            side=order_side,
            type=Client.ORDER_TYPE_MARKET,
            quantity=position['origQty']
        )

        return order

    def delete_pending(self, symbol, order_id):
        # Cancel a pending order
        result = self.client.cancel_order(symbol=symbol, orderId=order_id)
        if result['status'] == 'CANCELED':
            print(f"Order {order_id} deleted successfully.")
        else:
            print(f"Failed to delete order {order_id}.")

    def close_all(self, symbol):
        # Retrieve open positions
        positions = self.client.get_open_orders(symbol=symbol)
        # Close each position
        for position in positions:
            self.close_position(position)

    def close_limit(self, symbol):
        # Retrieve open orders for the symbol
        orders = self.client.get_open_orders(symbol=symbol)
        # Cancel each limit order
        for order in orders:
            if order['type'] == 'LIMIT':
                self.delete_pending(order['orderId'])

    def get_open_positions(self):
        # Retrieve all orders
        all_orders = self.client.get_all_orders(symbol=self.symbol)

        # Filter orders to find open positions
        open_positions = [order for order in all_orders if order['status'] in ['NEW', 'PARTIALLY_FILLED', 'PENDING']]

        return open_positions

    def get_bid_ask_prices(self, symbol_price):
        # Sort symbol price list by price
        sorted_prices = sorted(symbol_price, key=lambda x: x['price'])

        # The best bid price is the highest price in the list
        best_bid_price = float(sorted_prices[-1]['price'])

        # The best ask price is the lowest price in the list
        best_ask_price = float(sorted_prices[0]['price'])

        return best_bid_price, best_ask_price

    def run(self):
        while True:
            tick = self.client.get_order_book(symbol=self.symbol, limit=10)
            # Extract bid prices from the order book
            bid_prices = [float(bid[0]) for bid in tick['bids']]
            ask_prices = [float(bid[0]) for bid in tick['asks']]
            # Now you can access individual bid prices or use them as needed
            current_price_sell = bid_prices[0]
            current_price_buy = ask_prices[0]
            adj_sell = 1.2
            pct_change = 1

            # Place sell limit orders
            for i in range(self.n):
                price = ((pct_change / (
                        100 * 100)) * current_price_sell) * adj_sell * self.proportion + current_price_sell
                self.sell_limit(self.symbol, self.volume, price)
                pct_change += 1
                adj_sell += 0.2

            pct_change_2 = -1
            adj_buy = 1.2

            # Place buy limit orders
            for i in range(self.n):
                price = ((pct_change_2 / (
                        100 * 100)) * current_price_buy) * adj_buy * self.proportion + current_price_buy
                self.buy_limit(self.symbol, self.volume, price)
                pct_change_2 -= 1
                adj_buy += 0.2

            while True:
                # Fetch open positions
                open_positions = self.get_open_positions()
                if open_positions:
                    margin_s = self.cal_sell_margin(self.symbol)
                    margin_b = self.cal_buy_margin(self.symbol)

                    if margin_s > 0:
                        try:
                            pct_sell_profit = self.cal_pct_sell_profit(self.symbol)
                            if pct_sell_profit >= self.profit_target:
                                self.close_all(self.symbol)
                        except:
                            pass

                    if margin_b > 0:
                        try:
                            pct_buy_profit = self.cal_pct_buy_profit(self.symbol)
                            if pct_buy_profit >= self.profit_target:
                                self.close_all(self.symbol)
                        except:
                            pass

                    open_positions = self.get_open_positions()
                    if not open_positions:
                        self.close_limit(self.symbol)
                        break

                # Wait for a brief period before checking again
                time.sleep(10)  # Adjust this interval as needed
