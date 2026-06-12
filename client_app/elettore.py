import json
import time
import requests
from web3 import Web3
from crypto_utils import CryptoUtils

print("================================================================")
print(" CABINA ELETTORALE DIGITALE DELLO STUDENTE")
print("================================================================")

# 1. SETUP STUDENTE
MATRICOLA = "MAT_001"
SEGRETO_TOTP = b"SEGRETO_MFA_MARIO_2026"
IDP_URL = "https://127.0.0.1:5000/oauth/token"

# Generazione Chiave Effimera Studente (Lab 02)
sk_studente, pk_studente = CryptoUtils.generate_rsa_keypair()
pk_studente_pem = CryptoUtils.export_public_key(pk_studente)

# Generazione Chiave Commissione (In uno scenario reale verrebbe scaricata dalla bacheca)
_, pk_comm = CryptoUtils.generate_rsa_keypair()

print("\n>>> FASE 2: RICHIESTA TOKEN ALL'IdP (OIDC)")
# Calcoliamo il TOTP al volo per l'MFA
totp_code = CryptoUtils.generate_totp(SEGRETO_TOTP)
print(f"[{MATRICOLA}] Invio credenziali e TOTP ({totp_code}) all'IdP...")

# Facciamo la richiesta HTTPS al server IdP (ignoriamo verify=False solo per via del cert auto-firmato locale)
try:
    response = requests.post(IDP_URL, json={"client_id": MATRICOLA, "totp_code": totp_code}, verify=False)
    response.raise_for_status()
    token_data = response.json()
    
    t_id = token_data["id_token"]
    firma_idp_s = token_data["access_token"]
    print(f"[{MATRICOLA}] Token ottenuto con successo. Entro in cabina elettorale anonima.")
except requests.exceptions.RequestException as e:
    print(f"Errore di connessione all'IdP. Assicurati che server_oidc.py sia in esecuzione!")
    exit()

print("\n>>> FASE 3: ESPRESSIONE DEL VOTO E CIFRATURA")
preferenze = '["Lista_Onesta", "Lista_Onesta"]'

# Cifratura stocastica OAEP (Lab 02)
c_cifrato = CryptoUtils.rsa_encrypt_oaep(pk_comm, preferenze)
t_vote = int(time.time())
seq_voto = 1

# Firma PSS dello studente sul pacchetto
msg_studente = f"{c_cifrato}||{t_vote}||{seq_voto}||{firma_idp_s}"
sigma_studente = CryptoUtils.rsa_sign_pss(sk_studente, msg_studente)
print(f"[{MATRICOLA}] Voto cifrato (RSA-OAEP) e pacchetto firmato (RSA-PSS).")

print("\n>>> FASE 4: SOTTOMISSIONE SU BLOCKCHAIN TRAMITE WEB3")
# Connessione a Ganache
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
w3.eth.default_account = w3.eth.accounts[0]

# Carichiamo l'ABI generata nella Fase 1
with open("../contracts/abi.json", "r") as f:
    abi = json.load(f)

# INSERISCI QUI L'INDIRIZZO DEL TUO CONTRATTO (Quello ottenuto con deploy.py!)
CONTRACT_ADDRESS = "0x22A8cd2Db0D29fFcA5457F8ab337EfBAd341cd7A" 
urna_contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

print(f"[{MATRICOLA}] Invio transazione Web3 all'Urna Distribuita...")
try:
    tx_hash = urna_contract.functions.sottomettiVoto(
        t_id, c_cifrato, sigma_studente, t_vote, seq_voto, pk_studente_pem
    ).transact()
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"[{MATRICOLA}]  RICEVUTA: Voto registrato nel blocco N° {receipt.blockNumber}!")
except Exception as e:
    print(f" Transazione fallita: {e}")