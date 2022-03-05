from json import JSONDecodeError
import requests
from webull import paper_webull
import time
import math
api_key = "enter_API_key_here"
length_screen = 25

#Webull login
wb = paper_webull()
webull_email = 'webull_email'
webull_pass = 'webull_password'
wb.login(webull_email, webull_pass, 'device_name', 'login_code', 'question_number', 'question_answer')

#How we did today
print(wb.get_portfolio())

#Functions
def getFunction(symbol, time_period, function):
    #Uses API to find a function of a specific --returns -1 if not found in API
    interval = 'daily'
    url = f'https://www.alphavantage.co/query?function={function}&symbol={symbol}&interval={interval}&time_period={time_period}&series_type=close&apikey={api_key}'
    data = requests.get(url).json()
    while True:
        try:
            lastRefreshedDate = data['Meta Data']['3: Last Refreshed']
            if len(data[f'Technical Analysis: {function}']) == 0:
                return -1
            return data[f'Technical Analysis: {function}'][lastRefreshedDate][function]
        except KeyError:
            #Must wait a minute; wait and then recall
            print("Waiting 1 minute")
            time.sleep(60)
            data = requests.get(url).json()
def removefromFile(symbol, file_name):
    #Removes symbol from file
    old_file = open(file_name, "r")
    lines = old_file.readlines()
    old_file.close()
    new_file = open(file_name, "w")
    for line in lines:
        if line != symbol + "\n":
            new_file.write(line)
    new_file.close()
def stockList():
    #Generates list of stocks to consider
    stocks_watchlist = []
    watchlist = wb.get_watchlists()[4]['tickerList']
    for stock_data in watchlist:
        stocks_watchlist.append(stock_data['symbol'])
    if len(stocks_watchlist) > 0:
        return stocks_watchlist
    #Uses screener, shrinks list
    id_list = wb.run_screener(pct_chg_lte=-.7, pct_chg_gte=-.04, price_lte=15, price_gte=2000, region='United States')['tickerIdList']
    symbol_list = []
    for id in id_list:
        try:
            quote = wb.get_quote(tId=id)
            symbol = quote['symbol']
            chngRatio = quote['changeRatio']
            if float(chngRatio) < 0 and " " not in symbol:
                symbol_list.append(symbol)
        except JSONDecodeError:
            continue
    #Shrink list to 10
    if (length_screen > len(symbol_list)):
        return symbol_list
    else:
        increment = len(symbol_list) // length_screen
        stocks_list = []
        for i in range(0, increment*length_screen, increment):
            stocks_list.append(symbol_list[i])
        return stocks_list
def shouldAddToBuy(symbol):
    RSI = float(getFunction(symbol, 10, 'RSI'))
    if 0 < RSI < 30:
        return True
    return False
def shouldBuy(symbol):
    price = float(wb.get_quote(symbol)['close'])
    sma = float(getFunction(symbol, 10, 'SMA'))
    if (price > sma > 0):
        return True
    return False
def shouldRemoveToBuy(symbol):
    RSI = float(getFunction(symbol, 10, 'RSI'))
    if RSI > 40:
        return True
    return False
def shouldSell(symbol):
    price = wb.get_quote(symbol)['close']
    sma = getFunction(symbol, 10, 'SMA')
    if price < sma:
        return True
    return False
def buy(symbol) :
    buy_price = float(wb.get_quote(symbol)['close']) + 500
    wb.place_order(stock=symbol, price=buy_price, quant=20)
def sell(symbol) :
    sell_price = math.floor(float(wb.get_quote(symbol)['close']) * .98)
    wb.place_order(stock=symbol, price=sell_price, quant=20, action="SELL")


#Choose stocks to add to To_buy.txt
to_buy_file = open("To_buy.txt", "r+")
to_buy = to_buy_file.readlines()
just_added = []
stock_list = stockList()
print("Stock list located")
print(stock_list)
for stock in stock_list:
    if (stock + "\n") in to_buy:
        continue
    if shouldAddToBuy(stock):
        to_buy_file.write(stock + "\n")
        just_added.append(stock)
        print("To_buy added: " + stock)
to_buy_file.close()
print("Done adding stocks to To_buy")

#Delete items from To_buy.txt that should go
to_buy_file = open('To_buy.txt', "r")
to_buy = to_buy_file.readlines()
for stock in to_buy:
    stock = stock[:-1]
    if stock in just_added:
        continue
    if shouldRemoveToBuy(stock):
        removefromFile(stock, "To_buy.txt")
        print("To_buy removed: " + stock)
to_buy_file.close()
print("Done removing stocks from To_buy")

#Buy items from To_buy.txt that meet criteria. Add to Bought.txt. Remove from To_buy.txt
to_buy_file = open('To_buy.txt', "r")
to_buy = to_buy_file.readlines()
bought_file = open("Bought.txt", "r+")
bought = bought_file.readlines()
for stock in to_buy:
    if stock in bought:
        continue
    stock = stock[:-1]
    if shouldBuy(stock):
        buy(stock)
        bought_file.write(stock + "\n")
        removefromFile(stock, "To_buy.txt")
        print("Bought: " + stock)
to_buy_file.close()
bought_file.close()
print("Done buying stocks")

#Sell items from Bought.txt that meet criteria. Remove from Bought.txt
bought_file = open("Bought.txt", "r+")
bought = bought_file.readlines()
for stock in bought:
    stock = stock[:-1]
    if shouldSell(stock):
        sell(stock)
        removefromFile(stock, "Bought.txt")
        print("Sold: " + stock)
bought_file.close()
print("Done selling stocks")
