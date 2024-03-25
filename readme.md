Python dependencies: 

```
pip install eth-account
pip install python-dotenv

```


Quick guide:
1) clone repo
2) add .env file based on .env.example with your EOA private key, RPC address, the token address, and the gaslite drop address
3) update recipientsData.txt and amountsData.txt as necessary
4) run generateDrop.py - this looks at your current EOA nonce and generates all of the transactions, assigning them each a nonce to execute on (so we can resume if there's an issue without sending twice)
5) verify transactions.json if you'd like
6) run executeDrop.py - it will get your current EOA nonce and start executing from there