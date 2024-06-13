# Cake Bot

Allow to get list of cake orders from specified gsheet file

## How to run
```sh
git clone https://github.com/zaebee/cakebot.git && cd cakebot
virtualenv .venv && source .venv/bin/activate
./cakebot.py
```

## Secrets
You should create `.env` file and put tokens:
```
TG_TOKEN = ''
COHERE_TOKEN = ''
SHEET_ID = ''
```