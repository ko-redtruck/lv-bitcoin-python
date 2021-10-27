import requests
import json

class LightningWallet:
    def __init__(self):
        config_data = {}
        try:
            with open("./internal_data/lnbits_wallet.json") as json_file:
                config_data = json.load(json_file)
        except:
             with open("./internal_data/lnbits_wallet.json") as json_file:
                config_data = json.load(json_file)
                lnbits_host = input("Where is your lnbits instance hosted? (like https://lnbits.com)")
                lnbits_admin_key = input("Your lnbits admin key to access the wallet: ")
                config_data = {"host": lnbits_host,"admin_key":lnbits_admin_key}
                json.dump(config_data,json_file)

        self.admin_key = config_data["admin_key"]
        self.host = config_data["host"]

    def get_balance(self) -> int:
        headers = {
            "X-Api-Key": self.admin_key
        }
        r = requests.get(self.host + "/api/v1/wallet", headers=headers)
        if r.status_code == 200:
            r = r.json()
            return int(r["balance"]/1000)
        else:
            r = r.json()
            raise Exception(r)
            
    def pay(self,payment_request):
        json_body = {
            "out": True,
            "bolt11": payment_request
        }
        headers = {
            "X-Api-Key": self.admin_key
        }
        r = requests.post(self.host + "/api/v1/payments", json=json_body, headers=headers)
        if r.status_code == 201:
            r = r.json()
            return {"payment_hash": r["payment_hash"]}
        else:
            r = r.json()
            raise Exception(r)

    def create_invoice(self,amount):
        json_body = {
            "out": False,
            "amount": amount,
            "memo": "withdraw"
        }
        headers = {
            "X-Api-Key": self.admin_key
        }
        r = requests.post(self.host + "/api/v1/payments", json=json_body, headers=headers)
        if r.status_code == 201:
            r = r.json()
            return r["payment_request"]
        else:
            raise Exception(r.json())
