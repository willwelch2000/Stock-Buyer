from json import JSONDecodeError
import requests
from webull import paper_webull
import time
import math
personal_data_file = open("Personal_data.txt")
personal_data = personal_data_file.readlines()
personal_data_file.close()
api_key = personal_data[0][0:-1]
length_screen = 55

#Webull login
wb = paper_webull()
webull_email = personal_data[1][0:-1]
webull_pass = personal_data[2][0:-1]
mfa_pass = personal_data[3][0:-1]
security_question_id = personal_data[4][0:-1]
security_question_ans = personal_data[5:-1]
wb.login(webull_email, webull_pass, 'stockBuyer1', mfa_pass, security_question_id, security_question_ans)

#Summary of the day
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
            return float(data[f'Technical Analysis: {function}'][lastRefreshedDate][function])
        except KeyError:
            #Must wait a minute; wait and then recall
            print("Waiting 1 minute")
            time.sleep(60)
            data = requests.get(url).json()
def getPrice(symbol):
    #Accesses webull stock data to find price
    price = float(wb.get_quote(symbol)['close'])
    return price
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
    watchlists = wb.get_watchlists()
    list_name = "Consider"
    true_watchlist = []
    for watchlist in watchlists:
        if (watchlist['name'] == list_name):
            true_watchlist = watchlist['tickerList']
            break
    for stock_data in true_watchlist:
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
    RSI = getFunction(symbol, 10, 'RSI')
    if 0 < RSI < 30:
        return True
    return False
def shouldBuy(symbol):
    price = getPrice(symbol)
    sma = getFunction(symbol, 10, 'SMA')
    if (price > sma > 0):
        return True
    return False
def shouldRemoveToBuy(symbol):
    RSI = getFunction(symbol, 10, 'RSI')
    if RSI > 40:
        return True
    return False
def shouldSell(symbol):
    price = getPrice(symbol)
    sma = getFunction(symbol, 10, 'SMA')
    if price < sma:
        return True
    return False
def buy(symbol) :
    buy_price = getPrice(symbol) + 500
    wb.place_order(stock=symbol, price=buy_price, quant=20)
def sell(symbol) :
    sell_price = math.floor(getPrice(symbol) * .98)
    wb.place_order(stock=symbol, price=sell_price, quant=20, action="SELL")

#Choose stocks to add to "To buy" list
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
print("Done adding stocks to \"To buy\"")

#Delete items from "To buy" that should go
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
print("Done removing stocks from \"To buy\"")

#Buy items from "To buy" that meet criteria. Add to "Bought". Remove from "To buy"
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

#Sell items from "Bought" that meet criteria. Remove from "Bought"
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



