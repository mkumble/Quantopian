from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline import CustomFactor
import math
import numpy

def initialize(context):
    context.stocks = []
    attach_pipeline(make_pipeline(), 'my_pipeline')
    context.avg = 0
    context.lp = 0
    context.cp = 0
    context.pp = 0
    context.totalAmount = context.portfolio.portfolio_value
    context.slot = 0.375
    context.window = 1
    context.selectedStock = "none"
    context.pendingStock = "none"
    set_commission(commission.PerTrade(cost=0))

def make_pipeline():
    pipe = Pipeline()
    return pipe

def before_trading_start(context, data):
    context.leveraged_etfs = getStocksToTrade(context)
    context.doneTradingForDay = "no"

def handle_data(context, data):
    if hasNoPendingOrders(context.pendingStock):
        updateContextBoughtShareDetails(context, context.pendingStock)
        if context.selectedStock == "none":
            if context.doneTradingForDay == "no":
                for stock in context.leveraged_etfs:
                    updateContextPrices(data, context, stock)
                    if shouldBuyStocks(data, context,stock):
                        buyAmount = numOfStocksToBuy(context, stock)
                        buyStock(data, context, stock, buyAmount)
                        break
        else:
            updateContextPrices(data, context, context.selectedStock)
            if shouldSellStocks(context, context.selectedStock):
                sellStock(data, context, context.selectedStock)

def record_vars(context, data):
    # Record our variables.
    record(leverage=context.account.leverage)


def getStocksToTrade(context):
    leveragedETFs = []
    context.output = pipeline_output('my_pipeline')
    dt = get_datetime()
    for stock in context.output.index:
        if stock.sid in security_lists.leveraged_etf_list.current_securities(dt):
            leveragedETFs.append(stock)
    return leveragedETFs

def updateContextPrices(data,context, stock):
    stock_prices = data.history(stock, "price", 2, "1m")
    context.cp = stock_prices.iloc[-1]
    context.pp = stock_prices.iloc[-2]

def shouldBuyStocks(data, context, stock):
    low_history = data.history(stock, "price", 252, "1d")
    low = low_history.min()
    return context.avg==0 and context.cp - context.pp > 0 and context.cp <= low

def numOfStocksToBuy(context, stock):
    return context.totalAmount

def updateContextBoughtShareDetails(context, stock):
    if stock != "none":
        context.avg = context.portfolio.positions[stock].cost_basis
        context.selectedStock = stock
        context.pendingStock = "none"

def buyStock(data, context, stock, amount):
    if hasNoPendingOrders(stock):
        if data.can_trade(stock):
            order_value(stock, amount)
            context.pendingStock = stock

def shouldSellStocks(context, stock):
    return context.avg * context.portfolio.positions[stock].amount >=200

def sellStock(data,context, stock):
    if hasNoPendingOrders(stock):
        if data.can_trade(context.selectedStock):
            order_target_percent(context.selectedStock, 0.0)
            resetContextFields(context)
            context.doneTradingForDay = "yes"

def resetContextFields(context):
    context.avg = 0
    context.cp = 0
    context.pp = 0
    context.selectedStock = "none"

def hasNoPendingOrders(stock):
    return stock=="none" or len(get_open_orders(stock.sid)) == 0
