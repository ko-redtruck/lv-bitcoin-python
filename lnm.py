import requests
import json

class LNM:
    default_leverage = 50
    unit_margin = 41.8

    def __init__(self,LNMToken):
        self.LNMToken = LNMToken
        self.headers = {
            "Accept": "application/json",
            "Authorization": "Bearer "+self.LNMToken+""
        }

    def delete_running_pid(self):
        self.update_pid("")

    def update_pid(self,pid):
        with open('lnm.json', 'w') as outfile:
            json.dump({"running_pid":pid}, outfile)

    def get_running_pid(self):
        with open('lnm.json') as json_file:
            data = json.load(json_file)
            return data["running_pid"]

    def get_current_pl(self):
        running_positions = self.get_running_positions()
        if len(running_positions) == 0:
            return 0
        else:
            return running_positions[0]["pl"]

    def get_running_position_total_margin(self):
        running_positions = self.get_running_positions()
        margin = 0
        for position in running_positions:
            margin += position["margin"] + position["pl"]
        return margin

    def open_short(self,margin):
        url = "https://api.lnmarkets.com/v1/futures"
        payload = {
            "type": "m",
            "side": "s",
            "margin": margin,
            "leverage": 50
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer "+self.LNMToken
        }

        response = requests.request("POST", url, json=payload, headers=headers)

        data = response.json()
        self.update_pid(data["position"]["pid"])
        print("opened short position @{} USD with {} sats margin".format(data["position"]["price"],data["position"]["margin"]))
        return data

    def close_position(self,pid=""):
        url = "https://api.lnmarkets.com/v1/futures"
        if pid == "":
            pid = self.get_running_pid()

        querystring = {"pid":pid}
        response = requests.request("DELETE", url, headers=self.headers, params=querystring)
        self.delete_running_pid()
        data = response.json()
        print(data)
        print("closed position with a p&l of {} sats".format(data["pl"]))
        return response.json()

    def request_deposit_invoice(self,amount):
        url = "https://api.lnmarkets.com/v1/user/deposit"
        #min payment size of 1000 sats
        payload = {
            "amount": max(1000,amount),
            "unit": "sat"
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer "+self.LNMToken
        }

        response = requests.request("POST", url, json=payload, headers=headers)
        return response.json()["paymentRequest"]

    def withdraw(self,invoice):
        pass

    def get_running_positions(self):
        url = "https://api.lnmarkets.com/v1/futures"
        querystring = {"type":"running"}
        response = requests.request("GET", url, headers=self.headers, params=querystring)
        return response.json()

    def are_positions_running(self):
        if len(self.get_running_positions()) == 0:
            return False
        else:
            return True

    def get_available_margin(self):
        url = "https://api.lnmarkets.com/v1/user"
        response = requests.request("GET", url, headers=self.headers)
        return response.json()["balance"]

    def get_margin_used(self):
        running_positions = self.get_running_positions()
        margin = 0
        for position in running_positions:
            margin += position["margin"]
        return margin

    def get_position_coverage(self,balance):
        return (self.default_leverage* self.get_margin_used())/balance

    def is_position_coverage_within_range(self,range,balance):
        return abs(self.get_position_coverage(balance) - 1.0) <= range

    def get_optimal_margin(self,balance):
        return int((int(balance/self.unit_margin) * self.unit_margin))
    def get_optimal_coverage(self,balance):
        return self.get_optimal_margin(balance)/balance
    def get_current_price(self):
        url = "https://api.lnmarkets.com/v1/futures/history/bid-offer"
        response = requests.request("GET", url, headers=self.headers)
        return response.json()[0]["bid"]
