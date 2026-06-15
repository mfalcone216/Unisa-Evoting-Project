import json
import time
import secrets
from web3 import Web3
from crypto_utils import CryptoUtils

print("================================================================")
print(" SIMULAZIONE E-VOTING: BLOCKCHAIN, WEB3 E CRITTOGRAFIA RSA")
print("================================================================")

# 1. SETUP WEB3 E SMART CONTRACT
CONTRACT_ADDRESS = "0x22A8cd2Db0D29fFcA5457F8ab337EfBAd341cd7A" 
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
w3.eth.default_account = w3.eth.accounts[0] # Usiamo il primo account Ganache per pagare il Gas

with open("contracts/abi.json", "r") as f:
    abi = json.load(f)

urna_contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
print(f"Connesso a Ganache e allo Smart Contract in {CONTRACT_ADDRESS}")

# 2. SETUP ENTI (Generazione vere chiavi RSA)
print("\nGenerazione chiavi RSA a 2048 bit in corso...")
sk_idp, pk_idp = CryptoUtils.generate_rsa_keypair()
sk_comm, pk_comm = CryptoUtils.generate_rsa_keypair()
sk_studente, pk_studente = CryptoUtils.generate_rsa_keypair()
print("Chiavi PKI d'Ateneo e Studente generate con successo.")

# ---------------------------------------------------------
# FASE 2: AUTENTICAZIONE IdP (Simulazione OpenID Connect)
# ---------------------------------------------------------
print("\n>>> FASE 2: AUTENTICAZIONE FEDERATA OIDC")
matricola = "MAT_001"
print(f"Lo studente {matricola} effettua il login OIDC (MFA verificato).")

t_id = f"TID_{secrets.token_hex(4)}"
exp_time = int(time.time()) + 3600

# L'IdP firma il Token con RSA-PSS
msg_da_firmare_idp = f"{t_id}||{exp_time}"
firma_idp_s = CryptoUtils.rsa_sign_pss(sk_idp, msg_da_firmare_idp)
print(f"L'IdP rilascia il Token Anonimo {t_id} firmato con RSA-PSS. Applica Zero-Logging.")

# ---------------------------------------------------------
# FASE 3: PREPARAZIONE DEL VOTO (Client-Side)
# ---------------------------------------------------------
print("\n>>> FASE 3: CIFRATURA E FIRMA DEL VOTO (CLIENT)")
preferenze = '["Lista_Onesta", "Lista_Onesta"]'

# Cifratura stocastica OAEP con la chiave della commissione
c_cifrato = CryptoUtils.rsa_encrypt_oaep(pk_comm, preferenze)
t_vote = int(time.time())
seq_voto = 1

# Firma PSS dello studente sul pacchetto per garantirne l'integrità
msg_studente = f"{c_cifrato}||{t_vote}||{seq_voto}||{firma_idp_s}"
sigma_studente = CryptoUtils.rsa_sign_pss(sk_studente, msg_studente)
pk_studente_pem = CryptoUtils.export_public_key(pk_studente)

print("Voto cifrato in RSA-OAEP e firmato in RSA-PSS. Invio alla Blockchain...")

# ---------------------------------------------------------
# FASE 4: SOTTOMISSIONE SU BLOCKCHAIN TRAMITE WEB3
# ---------------------------------------------------------
print("\n>>> FASE 4: TRANSAZIONE WEB3 SULLO SMART CONTRACT")
try:
    # Chiamata alla funzione Solidity sottomettiVoto
    tx_hash = urna_contract.functions.sottomettiVoto(
        t_id, c_cifrato, sigma_studente, t_vote, seq_voto, pk_studente_pem
    ).transact()
    
    # Attendiamo che Ganache "mini" il blocco
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"VOTO ACCETTATO! Registrato nel blocco N° {receipt.blockNumber}")
    print(f"   Gas utilizzato per l'operazione: {receipt.gasUsed}")
except Exception as e:
    print(f"Transazione fallita: {e}")

# ---------------------------------------------------------
# FASE 5: SCRUTINIO FINALE (Lettura dallo Smart Contract)
# ---------------------------------------------------------
print("\n>>> FASE 5: LETTURA DALL'URNA E DECIFRATURA")
# Interroghiamo la blockchain per farci restituire tutti i voti
voti_estratti = urna_contract.functions.getTuttiVoti().call()
print(f"Estratti {len(voti_estratti)} voti cifrati dalla Blockchain.")

# La Commissione decifra con la sua chiave privata
voti_in_chiaro = CryptoUtils.rsa_decrypt_oaep(sk_comm, voti_estratti[0])
print("\n========================================")
print(" RISULTATI DELLO SCRUTINIO")
print("========================================")
print(f" -> Preferenze decifrate: {voti_in_chiaro}")
print("========================================\n")