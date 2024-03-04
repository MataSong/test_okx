# Quantum Dynamics Trading System (QDTS)
import ccxt
import threading
from queue import Queue
from typing import Union
from ccxt.base.types import OrderType, OrderSide
from const import (
    HIGHEST_PRICE, LOWEST_PRICE, CURRENT_PRICE, PERPETUAL_FEES, API_KEY, SECRET, PASSWORD, ENABLE_RATE_LIMIT, HIGH, LOW,
    LAST, SWAP, TOTAL_BALANCE, USED_BALANCE, FREE_BALANCE, TOTAL, USED, FREE
)


class QDTSBaseTransaction:
    def __init__(self, exchange_id, apiKey=None, secret=None, password=None, options=None):
        self.exchange_id = exchange_id
        self.apiKey = apiKey
        self.secret = secret
        self.password = password
        self.options = options if options is not None else {}
        self.exchange = getattr(ccxt, exchange_id)({
            API_KEY: apiKey, SECRET: secret, PASSWORD: password, ENABLE_RATE_LIMIT: True
        })

    def fetch_tickers(self) -> dict:
        return self.exchange.fetch_tickers()

    def fetch_balance(self) -> dict:
        return self.exchange.fetch_balance()

    def create_order(self, order_symbol, order_type, order_side, order_amount, order_price=None, order_params=None):
        return self.exchange.create_order(
            order_symbol, order_type, order_side, order_amount, order_price,
            order_params if order_params is not None else {}
        )

    def cancel_order(self, order_id, order_symbol=None):
        return self.exchange.cancel_order(order_id, order_symbol)


class QDTSSwapTransaction(QDTSBaseTransaction):

    def __init__(self, exchange_id, apiKey=None, secret=None, password=None, options=None):
        super().__init__(exchange_id, apiKey, secret, password, options)

    def fetch_swap_tickers(self, tickers_symbol: Union[None, str] = None) -> dict:
        tickers = self.exchange.fetch_tickers()

        highest_price = None
        lowest_price = None
        current_price = None

        for sym, ticker in tickers.items():
            if tickers_symbol and sym != tickers_symbol:
                continue

            if highest_price is None or ticker[HIGH] > highest_price:
                highest_price = ticker[HIGH]
            if lowest_price is None or ticker[LOW] < lowest_price:
                lowest_price = ticker[LOW]

            current_price = ticker[LAST]

        fees = self.exchange.fees
        perpetual_fees = fees.get(SWAP, {})

        return {
            HIGHEST_PRICE: highest_price,
            LOWEST_PRICE: lowest_price,
            CURRENT_PRICE: current_price,
            PERPETUAL_FEES: perpetual_fees
        }

    def fetch_swap_balance(self, balance_symbol: str = 'USDT') -> dict:
        balance_info = self.exchange.fetch_balance()
        balance_symbol = balance_symbol.upper()

        return {
            TOTAL_BALANCE: balance_info.get(TOTAL, {}).get(balance_symbol, 0),
            USED_BALANCE: balance_info.get(USED, {}).get(balance_symbol, 0),
            FREE_BALANCE: balance_info.get(FREE, {}).get(balance_symbol, 0)
        }


class QDTSBaseTrading:
    def __init__(self, threads_num: int, queue_size: int):
        self.threads_num = threads_num
        self.queue_size = queue_size
        self.flag = False
        self.queue = Queue(maxsize=queue_size)
        self.lock = threading.Lock()

    def start(self):
        self.flag = True
        for _ in range(self.threads_num):
            threading.Thread(target=self.add_queue_thread).start()
        threading.Thread(target=self.delete_queue_thread).start()

    def stop(self):
        self.flag = False

    def add_queue_thread(self):
        pass

    def delete_queue_thread(self):
        pass


class QDTSTransactionTrading(QDTSBaseTrading):

    def __init__(self, threads_num: int, queue_size: int, qdts_swap_transaction_obj: QDTSSwapTransaction):
        super().__init__(threads_num, queue_size)
        self.qdts_swap_transaction_obj = qdts_swap_transaction_obj

    def add_queue_thread(self):
        while self.flag:
            with self.lock:
                if not self.queue.full():
                    self.queue.put(
                        # 下单操作
                        # self.qdts_swap_transaction_obj.create_order()
                        1
                    )

    def delete_queue_thread(self):
        while self.flag:
            with self.lock:
                pass


if __name__ == '__main__':
    # 一个简单的永续下单操作

    stak_tickers_symbol = 'TURBO/USDT'
    stak_order_symbol = 'TURBO-USDT-SWAP'
    stak_side: OrderSide = 'buy'
    stak_type: OrderType = 'limit'
    stak_amount = 1
    stak_leverage = 3
    stak_params = {
        'lever': stak_leverage,
        'posSide': 'long',
        'tdMode': 'isolated',  # isolated or cross
    }

    qst_obj = QDTSSwapTransaction(
        **{
            'exchange_id': 'okx',
            'apiKey': 'xxxx',
            'secret': 'xxxx',
            'password': 'xxxx',
        }
    )
    print(f'已经入OKX交易所...')

    swap_balance_info = qst_obj.fetch_swap_balance()
    print(f'您的账户USDT可用余额为: {swap_balance_info[FREE_BALANCE]} 刀')

    swap_tickers_info = qst_obj.fetch_swap_tickers(tickers_symbol=stak_tickers_symbol)
    print(f'{stak_order_symbol}近期历史最高价格: {swap_tickers_info[HIGHEST_PRICE]} 刀')
    print(f'{stak_order_symbol}近期历史最低价格: {swap_tickers_info[LOWEST_PRICE]} 刀')
    print(f'{stak_order_symbol}当前价格: {swap_tickers_info[CURRENT_PRICE]} 刀')
    print(f'{stak_order_symbol}手续费: {swap_tickers_info[PERPETUAL_FEES]}')

    print(
        f'当前交易信息: {stak_order_symbol}, '
        f'订单类型为：限价单, '
        f'交易价格为: {swap_tickers_info[LOWEST_PRICE]} 刀, '
        f'交易方式为: 做多, '
        f'杠杆倍数: {stak_leverage}'
    )

    print(1 / 0.0000001)

    order_info = qst_obj.create_order(
        order_symbol=stak_order_symbol,
        order_type=stak_type,
        order_side=stak_side,
        order_amount=stak_amount,
        order_price=0.0000001,
        order_params=stak_params
    )
    print(f'Order info: {order_info}')
