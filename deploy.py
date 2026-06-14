import json
import os
from web3 import Web3
import solcx

# 1. Connessione a Ganache (Controllare che la porta sia quella giusta, 7545 o 8545)
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
if not w3.is_connected():
    print("ERRORE: Impossibile connettersi a Ganache. Controlla che sia aperto e la porta sia corretta.")
    exit()

print("Connesso a Ganache!")
w3.eth.default_account = w3.eth.accounts[0] 

# 2. Compilazione dello Smart Contract
print("Installazione compilatore Solidity (solo la prima volta richiede qualche secondo)...")
solcx.install_solc('0.8.0')
print("Compilazione dello Smart Contract in corso...")

with open("contracts/UrnaElettorale.sol", "r") as file:
    contract_source_code = file.read()

compiled_sol = solcx.compile_standard({
    "language": "Solidity",
    "sources": {"UrnaElettorale.sol": {"content": contract_source_code}},
    "settings": {"outputSelection": {"*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}}}
}, solc_version='0.8.0')

# Estrazione Bytecode e interfaccia ABI
bytecode = compiled_sol['contracts']['UrnaElettorale.sol']['UrnaElettorale']['evm']['bytecode']['object']
abi = compiled_sol['contracts']['UrnaElettorale.sol']['UrnaElettorale']['abi']

with open("contracts/abi.json", "w") as file:
    json.dump(abi, file)
print("Interfaccia ABI salvata in contracts/abi.json")

# 3. Deployment sulla Blockchain
print("Deployment sulla blockchain in corso...")
Urna = w3.eth.contract(abi=abi, bytecode=bytecode)
tx_hash = Urna.constructor().transact()

tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

with open("contract_address.txt", "w") as f:
    f.write(tx_receipt.contractAddress)

print("\nSMART CONTRACT DEPLOYATO CON SUCCESSO!")
print("="*60)
print(f"INDIRIZZO DEL CONTRATTO: {tx_receipt.contractAddress}")
print("="*60)
print("L'indirizzo è stato salvato automaticamente in 'contract_address.txt'!")