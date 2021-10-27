import requests
import json


class LightningWallet:
    def __init__(self):
        try:
            with open('./internal_data/wallet.json') as json_file:
                data = json.load(json_file)
                self.balance = data["balance"]
        except:
           with open('./internal_data/wallet.json',"w") as json_file:
                balance = int(input("Your balance in sats: "))
                self.balance = balance
                print("Thanks! You can update your balance in the file 'wallet.json' later.")
                json.dump({"balance":balance}, json_file)

    def get_balance(self) -> int:
       return self.balance
            
    def pay(self,payment_request):
        print("Please pay this payment request.")
        print(payment_request)
        user_input = ""
        while user_input != "y":
            user_input = input("Payment made successfully (y/n): ")
            
    def create_invoice(self,amount):
        invoice = input("Please input a invoice with a amount of {} sats: ".format(amount))
        return invoice
        
