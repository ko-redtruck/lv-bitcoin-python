# lv-bitcoin-python
A Python script to lower Bitcoin volatility with Futures

1. Clone
2. Create config.json


```javascript
{
    "LNMToken" : "Your lnmarkets.com API key",
    "balance" : 100000,
    "coverage_range" : 0.1,
    "lnbits_admin_key" : "your lnbits wallet admin key"
}
```

 without a LNbits admin key you are limited to your balance on lnmarkets.com

3. create a cron job to run it every 5-15 minutes

stats.csv will track information how well the script is performing
