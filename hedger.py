import math
import time
import csv
import json
from lnm import LNM
from lnbits_wallet import LNBits

class Hedger:
    balance = 18932
    coverage_range = 0.1
    #timestamp,value
    total_balance_cache = [0,0]

    def save_stats(self,price,total_balance,margin_used):
        with open('stats.csv','a') as fd:
            fd.write("{},{},{},{:.2f},{} \n".format(time.time(),price,total_balance,(total_balance/(1*10**8))*price,margin_used))

    def __init__(self):
        with open('config.json') as json_file:
            data = json.load(json_file)
            self.balance = data["balance"]
            self.coverage_range = data["coverage_range"]
            self.exchange = LNM(data["LNMToken"])
            self.lightning_wallet = LNBits(data["lnbits_admin_key"])

    def update(self):
        total_balance = self.get_total_balance()
        price = self.exchange.get_current_price()
        margin_used = self.exchange.get_margin_used()

        self.save_stats(price,total_balance,margin_used)

        print("running with {:.2f}% short hedge".format(self.exchange.get_position_coverage(self.get_current_balance())*100))
        print("current total balance of {} sats with value of: {:.2f} USD with Bitcoin price @{} USD".format(total_balance,self.get_balance_usd_value(),self.exchange.get_current_price()))

        if self.exchange.are_positions_running() == True:
            if self.exchange.is_position_coverage_within_range(self.coverage_range,self.get_current_balance()) == False:
                print("short running but not within the coverage range!")
                self.exchange.close_position()
                self.open_short(int(self.get_current_balance()/self.exchange.default_leverage))
        else:
            short_data = self.open_short(int(self.get_current_balance()/self.exchange.default_leverage))

    def get_total_balance(self):
        #save total balance for 10 seconds
        if time.time() - self.total_balance_cache[0] < 10:
            return self.total_balance_cache[1]
        else:
            total_balance = self.balance + self.exchange.get_available_margin() + self.exchange.get_running_position_total_margin()
            self.total_balance_cache = [time.time(),total_balance]
            return total_balance

    def get_current_balance(self):
        return self.balance + self.exchange.get_available_margin() + self.exchange.get_running_position_total_margin()

    def get_balance_usd_value(self):
        total_balance = self.get_total_balance()
        current_bid_price = self.exchange.get_current_price()
        return (total_balance/(1*10**8)) * current_bid_price



    def open_short(self,required_margin):
        #check if the margin is available
        missing_funds = required_margin - self.exchange.get_available_margin()
        print("missing {} sats to open a short position of {} sats".format(missing_funds,required_margin))
        if missing_funds > 0:
            invoice = self.exchange.request_deposit_invoice(missing_funds)
            self.lightning_wallet.pay(invoice)
            print("deposited {} sats on lnmarkets.com".format(missing_funds))
        self.exchange.open_short(required_margin)

    def add(self,x):
        self.balance += x
        self.fund_lnm()

    def remove(self,x):
        self.balance -= x
        #self.withdraw_lnm()

    def _get_min_total_required_balance(self):
        return math.ceil(self.balance*0.02)

    def fund_lnm(self):
        missing_funds = self._get_min_total_required_balance() - self.margin_used
        if missing_funds > 0:
            self.margin_available = max(1000,missing_funds) + self.margin_available
            print("lnm missing",max(1000,missing_funds),"sats")
        print("balance:",self.balance," lnm available:",self.margin_available, " lnm margin used:",self.margin_used)

    def withdraw_lnm(self):
        unnecessary_funds = self.lnm_balance - self._get_min_total_required_balance()
        if unnecessary_funds >= 1000:
            print("withdrawing",unnecessary_funds," sats from lnmarkets")
            self.lnm_balance -= unnecessary_funds
        print("balance:",self.balance," lnm:",self.lnm_balance)


if __name__ == "__main__":
    h = Hedger()
    h.update()
