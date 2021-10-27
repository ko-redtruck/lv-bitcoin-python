# lv-bitcoin-python
A Python script to lower Bitcoin volatility with Futures (lnmarkets.com)

### Setup instructions for Linux
1. Clone the repository
```shell
git clone https://github.com/ko-redtruck/lv-bitcoin-python.git && cd ./lv-bitcoin-python
```
2. Optional but recommended: Install python-crontab to automatically schedule the cronjobs necessary
```shell
pip3 install python-crontab
```
3. Run and follow the instructions
```shell
python3 hedger.py
```

Single command setup

```shell
git clone https://github.com/ko-redtruck/lv-bitcoin-python.git && cd ./lv-bitcoin-python && pip3 install python-crontab && python3 hedger.py
```
