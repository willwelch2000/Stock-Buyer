import sqlite3 as sl
from sqlite3 import Error

class ManageDb():

    def __init__(self, file_path):
        self.establish_connection(file_path)
        create_to_buy_table_sql = '''CREATE TABLE IF NOT EXISTS to_buy (
                                        ticker text NOT NULL
                                     );'''
        self.run_sql(create_to_buy_table_sql)

    def establish_connection(self, file_path):
        self.conn = None
        try:
            self.conn = sl.connect(file_path)
        except Error as e:
            print(e)

    def close_connection(self):
        self.conn.close()

    # Returns cursor
    def run_sql(self, command, object=None, commit=False):
        try:
            c = self.conn.cursor()
            if (object):
                c.execute(command, object)
            else:
                c.execute(command)
            if (commit):
                self.conn.commit()
            return c
        except Error as e:
            print(e)

    def insert_to_buy(self, ticker):
        insert_stock_to_buy_sql = '''INSERT INTO to_buy (ticker)
                                VALUES (?);
                           '''
        self.run_sql(insert_stock_to_buy_sql, (ticker,), True)

    def delete_to_buy(self, ticker):
        delete_stock_to_buy_sql = '''DELETE FROM to_buy
                                        WHERE ticker = ?;
                                  '''
        self.run_sql(delete_stock_to_buy_sql, (ticker,), True)

    def delete_all_to_buy(self):
        delete_all_to_buy_sql = '''DELETE FROM to_buy;'''
        self.run_sql(delete_all_to_buy_sql, None, True)

    def select_all_to_buy(self):
        select_all_to_buy_sql = '''SELECT ticker FROM to_buy;'''
        c = self.run_sql(select_all_to_buy_sql)
        return c.fetchall()