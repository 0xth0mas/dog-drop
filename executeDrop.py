from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3, HTTPProvider
import json
from dotenv import dotenv_values
import time

config = dotenv_values(".env")

CHAIN_ID = 8453

gasliteDropABI = json.loads('[{"inputs":[{"internalType":"address","name":"_token","type":"address"},{"internalType":"address[]","name":"_addresses","type":"address[]"},{"internalType":"uint256[]","name":"_amounts","type":"uint256[]"},{"internalType":"uint256","name":"_totalAmount","type":"uint256"}],"name":"airdropERC20","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"_nft","type":"address"},{"internalType":"address[]","name":"_addresses","type":"address[]"},{"internalType":"uint256[]","name":"_tokenIds","type":"uint256[]"}],"name":"airdropERC721","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address[]","name":"_addresses","type":"address[]"},{"internalType":"uint256[]","name":"_amounts","type":"uint256[]"}],"name":"airdropETH","outputs":[],"stateMutability":"payable","type":"function"}]')
erc20ABI = json.loads('[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"AllowanceOverflow","type":"error"},{"inputs":[],"name":"AllowanceUnderflow","type":"error"},{"inputs":[],"name":"InsufficientAllowance","type":"error"},{"inputs":[],"name":"InsufficientBalance","type":"error"},{"inputs":[],"name":"InvalidPermit","type":"error"},{"inputs":[],"name":"PermitExpired","type":"error"},{"inputs":[],"name":"TotalSupplyOverflow","type":"error"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"result","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"result","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"result","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"result","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"pure","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"result","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}]')

senderPK = config["SENDER_PK"]
rpcURL = config["RPC_URL"]
tokenAddress = config["TOKEN_ADDRESS"]
gasliteDropAddress = config["GASLITE_DROP_ADDRESS"]

def main() -> None:
    # account to send the transfer and sign transactions
    sender: LocalAccount = Account.from_key(senderPK)
    w3 = Web3(HTTPProvider(rpcURL))
    gasliteDrop = w3.eth.contract(address=gasliteDropAddress, abi=gasliteDropABI)

    transactionsFile = open("transactions.json", "r")
    transactions = json.load(transactionsFile)

    nonce = w3.eth.get_transaction_count(sender.address)
    print(f"Start nonce: {nonce}")

    while True: 
        strNonce = str(nonce)
        if not strNonce in transactions.keys():
            print("Finished.")
            return
        
        raw_tx = None
        if "approval" in transactions[strNonce].keys():
            raw_tx = transactions[strNonce]["approval"]
        else:
            drop_tx = gasliteDrop.functions.airdropERC20(
                transactions[strNonce]["drop"]["tokenAddress"], 
                transactions[strNonce]["drop"]["recipients"], 
                transactions[strNonce]["drop"]["amounts"],
                transactions[strNonce]["drop"]["totalAmount"]
            ).build_transaction({'nonce': nonce, 'gas': 24000000})
            raw_tx = w3.eth.account.sign_transaction(drop_tx, senderPK).rawTransaction
        
        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        
        print(f'transaction submitted: {tx_hash.hex()}')

        try: 
            w3.eth.wait_for_transaction_receipt(tx_hash)
        except: 
            print(f'failed to mine transaction')
            return
        
        nonce = nonce + 1
        time.sleep(2.0)

if __name__ == "__main__":
    main()