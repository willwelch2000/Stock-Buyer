from json import JSONDecodeError
import json
import requests
from webull import paper_webull
import time
import math
from managedb import ManageDb

#Parameters
length_screen = 40

#Functions
def getFunction(symbol, time_period, function):
    #Uses API to find a function of a specific stock--returns -1 if not found in API
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
def getWatchlist(name):
    watchlists = wb.get_watchlists()
    correct_list = []
    for watchlist in watchlists:
        if (watchlist['name'] == name):
            correct_list = watchlist['tickerList']
            break
    stock_list = []
    for stock_data in correct_list:
        stock_list.append(stock_data['symbol'])
    return stock_list
def getConsiderList():
    #Generates list of stocks to consider

    #Checks if the watchlist "Consider" on webull profile is nonempty--if so, it returns this
    list_name = "Consider"
    stocks_watchlist = getWatchlist(list_name)
    if len(stocks_watchlist) > 0:
        return stocks_watchlist

    #Otherwise--uses a screening tool
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
    #Shrink list to maximum size
    if (length_screen > len(symbol_list)):
        return symbol_list
    else:
        increment = len(symbol_list) // length_screen
        stocks_list = []
        for i in range(0, increment*length_screen, increment):
            stocks_list.append(symbol_list[i])
        return stocks_list
def getBoughtList():
    positions = wb.get_positions()
    stock_list = []
    for position in positions:
        stock_list.append(position['ticker']['symbol'])
    return stock_list
def getToBuyList():
    db_manager = ManageDb(r"C:\Users\willw\PycharmProjects\stockBuyer1\db\stockData.db")
    db_list = db_manager.select_all_to_buy()
    to_buy_list = list(map(lambda stock_obj: stock_obj[0], db_list))
    db_manager.close_connection()
    return to_buy_list
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
def shouldAddToBuy(symbol):
    rsi = getFunction(symbol, 10, 'RSI')
    if 0 < rsi < 30:
        return True
    return False
def shouldRemoveToBuy(symbol):
    rsi = getFunction(symbol, 10, 'RSI')
    if rsi > 40:
        return True
    return False
def addToBuy(symbol):
    db_manager = ManageDb(r"C:\Users\willw\PycharmProjects\stockBuyer1\db\stockData.db")
    db_manager.insert_to_buy(symbol)
    db_manager.close_connection()
def deleteToBuy(symbol):
    db_manager = ManageDb(r"C:\Users\willw\PycharmProjects\stockBuyer1\db\stockData.db")
    db_manager.delete_to_buy(symbol)
    db_manager.close_connection()
def shouldBuy(symbol):
    price = getPrice(symbol)
    sma = getFunction(symbol, 10, 'SMA')
    if (price > sma > 0):
        return True
    return False
def shouldSell(symbol):
    price = getPrice(symbol)
    sma = getFunction(symbol, 10, 'SMA')
    if price < sma:
        return True
    return False
def buy(symbol) :
    buy_price = getPrice(symbol)
    wb.place_order(stock=symbol, price=buy_price, quant=20)
def sell(symbol) :
    sell_price = math.floor(getPrice(symbol) * .98)
    wb.place_order(stock=symbol, price=sell_price, quant=20, action="SELL")

#Organize personal data
personal_data_file = open("personalData.json")
personal_data = json.load(personal_data_file)
api_key = personal_data['apiKey']
email = personal_data['email']
password = personal_data['password']
mfa_pass = personal_data['mfaPass']
security_question_id = personal_data['securityQuestionId']
security_ans = personal_data['securityAnswer']

#Webull login-- 'stockBuyer1' is the name that shows up on Webull
wb = paper_webull()
wb.login(email, password, 'stockBuyer1', mfa_pass, security_question_id, security_ans)

#Summary of the day
print(wb.get_portfolio())

#Choose stocks to add to "To buy"
to_buy = getToBuyList()
just_added = []
consider_list = getConsiderList()
print("Consider list located")
print(consider_list)
for stock in consider_list:
    if stock in to_buy:
        continue
    if shouldAddToBuy(stock):
        addToBuy(stock)
        just_added.append(stock)
        print("To_buy added: " + stock)
print("Done adding stocks to \"To buy\"")

#Delete items from "To buy" that should go
to_buy = getToBuyList()
for stock in to_buy:
    if stock in just_added:
        continue
    if shouldRemoveToBuy(stock):
        deleteToBuy(stock)
        print("To_buy removed: " + stock)
print("Done removing stocks from \"To buy\"")

#Buy items from "To buy" that meet criteria. Remove from "To buy"
to_buy = getToBuyList()
bought = getBoughtList()
for stock in to_buy:
    if stock in bought:
        continue
    if shouldBuy(stock):
        buy(stock)
        deleteToBuy(stock)
        print("Bought: " + stock)
print("Done buying stocks")

#Sell items from bought list that meet criteria
bought = getBoughtList()
for stock in bought:
    if shouldSell(stock):
        sell(stock)
        print("Sold: " + stock)
print("Done selling stocks")



