from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3, HTTPProvider, constants
import json
from dotenv import dotenv_values

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
    token = w3.eth.contract(address=tokenAddress, abi=erc20ABI)

    amountsFile = open("amountsData.txt", "r") 
    recipientsFile = open("recipientsData.txt", "r") 

    amounts = amountsFile.readlines()
    recipients = recipientsFile.readlines()

    print(f'# of recipients: {len(amounts)}')

    if not len(amounts) == len(recipients):
        print("Invalid lists, lengths do not match.")
        return
    
    for index in range(0, len(amounts)): 
        amounts[index] = int(amounts[index][:-1])
        recipients[index] = w3.to_checksum_address(recipients[index][:-1])

    nonce = w3.eth.get_transaction_count(sender.address)
    print(f"Sender address: {sender.address}")
    print(f"Start nonce: {nonce}")
    
    transactions = {}

    approve_tx = token.functions.approve(w3.to_checksum_address(gasliteDropAddress), int(constants.MAX_INT, 16)).build_transaction({'from': sender.address, 'nonce': nonce})
    signed_approve_tx = w3.eth.account.sign_transaction(approve_tx, senderPK)
    transactions[nonce] = {"approval": signed_approve_tx.rawTransaction.hex()}

    nonce = nonce + 1


    for startIndex in range(0, len(amounts), 750):
        print(f'Working on range start: {startIndex}')
        endIndex = startIndex + 750
        if endIndex > len(amounts):
            endIndex = len(amounts)
        
        amountsSlice = amounts[startIndex:endIndex]
        recipientsSlice = recipients[startIndex:endIndex]
        
        totalAmount = 0
        for amount in amountsSlice: 
            totalAmount = totalAmount + amount


        #drop_tx = gasliteDrop.functions.airdropERC20(tokenAddress, recipientsSlice, amountsSlice, totalAmount).build_transaction({'nonce': nonce})
        #signed_drop_tx = w3.eth.account.sign_transaction(drop_tx, senderPK)
        transactions[nonce] = {"drop": {"tokenAddress": tokenAddress, "recipients": recipientsSlice, "amounts": amountsSlice, "totalAmount": totalAmount}}

        if startIndex == 0:
            print(transactions[nonce])

        nonce = nonce + 1
    
    
    with open('transactions.json', 'w', encoding='utf-8') as f:
        json.dump(transactions, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()