import time
import json
import pathlib
import time
import os

class Hedger:
    balance = 18932
    #timestamp,value
    total_balance_cache = [0,0]

    def save_stats(self,price,total_balance,margin_used):
        try:
            with open('./internal_data/stats.csv','a') as fd:
                fd.write("{},{},{},{:.2f},{} \n".format(time.time(),price,total_balance,(total_balance/(1*10**8))*price,margin_used))
        except IOError:
            with open("./internal_data/sats.csv","w") as fd:
                fd.write("{},{},{},{:.2f},{} \n".format(time.time(),price,total_balance,(total_balance/(1*10**8))*price,margin_used))

    def check_service_availability(self):
        try:
            balance = self.lightning_wallet.get_balance()
            print("Lightning wallet working with active balance of {} sats".format(balance))
        except:
            raise Exception('Your Lightning wallet is not working')
        try:
            exchange_balance = self.exchange.get_available_margin()
            print("lnmarkets.com active with balance of {} sats".format(exchange_balance))
        except:
            raise Exception('lnmarkets not working')

    def __init__(self,Exchange,LightningWallet):
        data = {}
        try:
            with open('./internal_data/config.json') as json_file:
                data = json.load(json_file)
        except IOError:
            
            data = {
                "coverage_range" : 0.1,
                "coverage_target" : 1.0
            }

            with open('./internal_data/config.json', 'w') as outfile:
                json.dump(data, outfile)

        finally:
            self.coverage_range = data["coverage_range"]
            self.coverage_target = data["coverage_target"]
            self.exchange = Exchange()
            self.lightning_wallet = LightningWallet()
            self.check_service_availability()

    def update(self):
        total_balance = self.get_balance()

        if total_balance == 0:
            print("please deposit sats in your wallet")
            return

        price = self.exchange.get_current_price()
        margin_used = self.exchange.get_used_margin()

        self.save_stats(price,total_balance,margin_used)

        print("running with {:.2f}% short hedge".format(self.__get_position_coverage()*100))
        print("current total balance of {} sats with value of: {:.2f} USD with Bitcoin price @{} USD".format(total_balance,self.get_balance_usd_value(),self.exchange.get_current_price()))


        #decuct 10 sats buffer for fees
        available_margin = self.exchange.get_available_margin() - 10
        pl = self.exchange.get_pl()
        if available_margin > self.exchange.min_withdrawable or available_margin + pl > self.exchange.min_withdrawable:
            if pl > 0:
                self.exchange.close_position()
            self.withdraw_from_exchange(max(available_margin,pl+available_margin))
            
        if self.exchange.is_positon_running() == True:
            if self.__is_position_within_coverage_range() == False:
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
        if missing_funds > 0:
            print("missing {} sats to open a short position of {} sats".format(missing_funds,required_margin))
            invoice = self.exchange.request_deposit_invoice(missing_funds)
            self.lightning_wallet.pay(invoice)
            print("deposited {} sats on lnmarkets.com".format(missing_funds))

        self.exchange.open_short(required_margin)

    
    def withdraw_from_exchange(self,amount):
        print("withdrawing {} sats from lnmarkets.com".format(amount))
        invoice = self.lightning_wallet.create_invoice(amount)
        self.exchange.withdraw(invoice)
    
    def __get_position_coverage(self):
        return (self.exchange.default_leverage * self.exchange.get_used_margin())/(self.lightning_wallet.get_balance()+self.exchange.get_available_margin()+self.exchange.get_used_margin())

    def __is_position_within_coverage_range(self):
        return abs(self.__get_position_coverage() - self.coverage_target) <= self.coverage_range

    def __get_required_margin(self):
        return int(self.get_balance()/self.exchange.default_leverage)


def __ask_user(question_string) -> bool:
    user_input = ""
    for i in range(5):
        user_input = input(question_string + " (y/n)")
        if user_input == "y":
            return True
        elif user_input == "n":
            return False
    return False

if __name__ == "__main__":
    if not os.path.exists("./internal_data"):
        os.mkdir("./internal_data")

    try:
        with open('./internal_data/module_config.json') as json_file:
            data = json.load(json_file)

            #hedge duration over
            if (time.time() - data["start_timestamp"]) / 60*60*24 > data["hedge_duration"]:
                if data["automatic_schedulling"] == True:
                    CronTab = __import__("crontab").CronTab
                    cron = CronTab(user=True)
                    working_directory = pathlib.Path().resolve()
                    cron.remove_all(comment='cd {} && python3 ./hedger.py'.format(working_directory))

            h = Hedger(__import__(data["exchange_module"]).Exchange,__import__(data["lightning_wallet_module"]).LightningWallet)
            h.update()
    except:
        print("No config files found. Starting new configuration process")

        lightning_wallet_module_name ="manual_wallet"
        LightningWallet = __import__(lightning_wallet_module_name).LightningWallet
        lightning_wallet_module_name = ""
        if __ask_user("Do you want to use lnbits as your backend? (alternative: manual backend)"):
            lightning_wallet_module_name = "lnbits_wallet"
            LightningWallet = __import__(lightning_wallet_module_name).LightningWallet            
        
        exchange_module_name = "lnm"
        Exchange = __import__(exchange_module_name).Exchange

        hedge_duration = int(input("How long do you want to hedge your position? (in days)"))

        print("To work this script has to be run every 10-15 minutes.")
        automatic_schedulling = False
        if __ask_user("Do you want to automatically schedule a cronjob to do that? (requires the crontab module)"):
            CronTab = __import__("crontab").CronTab
            cron = CronTab(user=True)

            working_directory = pathlib.Path().resolve()
            cron.remove_all(command='cd {} && python3 ./hedger.py'.format(working_directory))
            job = cron.new(command='cd {} && python3 ./hedger.py'.format(working_directory))
            job.minute.every(10)
            cron.write()
            automatic_schedulling = True

        with open("./internal_data/module-config.json","w") as json_file:
            json.dump({
                "lightning_wallet_module" : lightning_wallet_module_name,
                "exchange_module" : exchange_module_name,
                "hedge_duration" : hedge_duration,
                "start_timestamp" : time.time(),
                "automatic_schedulling" : automatic_schedulling
            },json_file)

        h = Hedger(Exchange,LightningWallet)
        h.update()