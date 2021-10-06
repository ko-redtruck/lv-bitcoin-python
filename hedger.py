import time
import json
from lnm import LNM
from lnbits_wallet import LNBits

class Hedger:
    balance = 18932
    #timestamp,value
    total_balance_cache = [0,0]

    def save_stats(self,price,total_balance,margin_used):
        try:
            with open('stats.csv','a') as fd:
                fd.write("{},{},{},{:.2f},{} \n".format(time.time(),price,total_balance,(total_balance/(1*10**8))*price,margin_used))
        except IOError:
            with open("sats.csv","w") as fd:
                fd.write("{},{},{},{:.2f},{} \n".format(time.time(),price,total_balance,(total_balance/(1*10**8))*price,margin_used))

    def check_service_availability(self):
        try:
            balance = self.lightning_wallet.get_balance()
            print("LNBits active with balance of {} sats".format(balance))
        except:
            raise Exception('LNBits not working')
        try:
            exchange_balance = self.exchange.get_available_margin()
            print("lnmarkets.com active with balance of {} sats".format(exchange_balance))
        except:
            raise Exception('lnmarkets not working')

    def __init__(self):
        data = {}
        try:
            with open('config.json') as json_file:
                data = json.load(json_file)
        except IOError:
            print("Hello, this script will need a few infos to start working :)")
            lnbits_host = input("Where is your lnbits instance hosted? (like https://lnbits.com)")
            lnbits_admin_key = input("Your lnbits admin key to access the wallet: ")
            LNMToken = input("Your lnmarkets.com token with all scopes (Withdraw, Deposit, Futures, User): ")

            data = {
                "lnbits_admin_key" : lnbits_admin_key,
                "lnbits_host" : lnbits_host,
                "LNMToken" : LNMToken,
                "coverage_range" : 0.1,
                "coverage_target" : 1.0
            }

            with open('config.json', 'w') as outfile:
                json.dump(data, outfile)


            print("We have saved your information in the file config.json. You can change your lnmarkets account or lnbits wallet there anytime.")

        finally:
            self.coverage_range = data["coverage_range"]
            self.coverage_target = data["coverage_target"]
            self.exchange = LNM(data["LNMToken"])
            self.lightning_wallet = LNBits(data["lnbits_admin_key"],data["lnbits_host"])
            self.check_service_availability()

    def update(self):
        total_balance = self.get_balance()
        price = self.exchange.get_current_price()
        margin_used = self.exchange.get_used_margin()

        self.save_stats(price,total_balance,margin_used)

        print("running with {:.2f}% short hedge".format(self.__get_position_coverage()*100))
        print("current total balance of {} sats with value of: {:.2f} USD with Bitcoin price @{} USD".format(total_balance,self.get_balance_usd_value(),self.exchange.get_current_price()))

        if self.exchange.is_positon_running() == True:
            if self.__get_required_margin() == False:
                print("short running but not within the coverage range!")
                self.exchange.close_position()
                self.open_short(self.__get_required_margin())
        else:
            self.open_short(self.__get_required_margin())

    def get_balance(self):
        #save total balance for 10 seconds
        if time.time() - self.total_balance_cache[0] < 10:
            return self.total_balance_cache[1]
        else:
            total_balance = self.lightning_wallet.get_balance() + self.exchange.get_available_margin() + self.exchange.get_used_margin() + self.exchange.get_pl()
            self.total_balance_cache = [time.time(),total_balance]
            return total_balance

    def get_balance_usd_value(self):
        total_balance = self.get_balance()
        current_bid_price = self.exchange.get_current_price()
        return (total_balance/(1*10**8)) * current_bid_price



    def open_short(self,required_margin):
        #ensure funding
        missing_funds = required_margin - self.exchange.get_available_margin()
        print("missing {} sats to open a short position of {} sats".format(missing_funds,required_margin))
        if missing_funds > 0:
            invoice = self.exchange.request_deposit_invoice(missing_funds)
            self.lightning_wallet.pay(invoice)
            print("deposited {} sats on lnmarkets.com".format(missing_funds))

        self.exchange.open_short(required_margin)

    """
    def withdraw_lnm(self):
        unnecessary_funds = self.lnm_balance - self._get_min_total_required_balance()
        if unnecessary_funds >= 1000:
            print("withdrawing",unnecessary_funds," sats from lnmarkets")
            self.lnm_balance -= unnecessary_funds
        print("balance:",self.lightning_wallet.get_balance()," lnm:",self.lnm_balance)
    """
    def __get_position_coverage(self):
        return (self.exchange.default_leverage * self.exchange.get_used_margin())/(self.lightning_wallet.get_balance()+self.exchange.get_available_margin()+self.exchange.get_used_margin())

    def __get_required_margin(self):
        return abs(self.__get_position_coverage() - self.coverage_target) <= self.coverage_range

    def __get_required_margin(self):
        return int(self.get_balance()/self.exchange.default_leverage)


if __name__ == "__main__":
    h = Hedger()
    h.update()
