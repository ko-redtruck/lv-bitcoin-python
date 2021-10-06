import requests


class LNBits:
    def __init__(self,admin_key,host):
        self.admin_key = admin_key
        self.host = host

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
