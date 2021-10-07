import requests
import json

class LNM:
    default_leverage = 50
    unit_margin = 41.8
    min_withdrawable = 1000

    def __init__(self,LNMToken):
        self.LNMToken = LNMToken
        self.headers = {
            "Accept": "application/json",
            "Authorization": "Bearer "+self.LNMToken+""
        }
        self.pid = self.__get_pid()

    def __delete_running_pid(self):
        self.__update_pid("")

    def __update_pid(self,pid):
        with open('lnm.json', 'w') as outfile:
            self.pid = pid
            json.dump({"running_pid":pid}, outfile)

    def __get_pid(self):
        try:
            with open('lnm.json') as json_file:
                data = json.load(json_file)
                return data["running_pid"]
        except:
            return ""

    def __get_position(self):
        url = "https://api.lnmarkets.com/v1/futures"
        querystring = {"type":"running"}
        response = requests.request("GET", url, headers=self.headers, params=querystring)
        positions = response.json()

        if len(positions)==0:
            return None

        for p in positions:
            if p["pid"] == self.pid:
                return p

        return None

    def get_pl(self) -> int:
        try:
            return self.__get_position()["pl"]
        except:
            return 0

    def get_available_margin(self) -> int:
        url = "https://api.lnmarkets.com/v1/user"
        response = requests.request("GET", url, headers=self.headers)
        return response.json()["balance"]

    def get_used_margin(self) -> int:
        try:
            return self.__get_position()["margin"]
        except:
            return 0

    def open_short(self,margin) -> dict:
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
        self.__update_pid(data["position"]["pid"])
        print("opened short position @{} USD with {} sats margin".format(data["position"]["price"],data["position"]["margin"]))
        return data

    def close_position(self,pid=None):
        if pid is None:
            pid = self.pid

        url = "https://api.lnmarkets.com/v1/futures"
        querystring = {"pid":pid}
        response = requests.request("DELETE", url, headers=self.headers, params=querystring)
        self.__delete_running_pid()
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
        url = "https://api.lnmarkets.com/v1/user/withdraw"
        payload = {"invoice": invoice}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer "+self.LNMToken
        }

        response = requests.request("POST", url, json=payload, headers=headers)

    def is_positon_running(self):
        return self.__get_position() is not None

    def get_current_price(self):
        url = "https://api.lnmarkets.com/v1/futures/history/bid-offer"
        response = requests.request("GET", url, headers=self.headers)
        return response.json()[0]["bid"]
