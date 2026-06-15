import json
import time
import requests
import urllib3
from flask import Flask, render_template, request, jsonify
from web3 import Web3
from crypto_utils import CryptoUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

IDP_URL = "https://127.0.0.1:5000/oauth/token"

# Variabili globali per mantenere lo stato della sessione del client
# (In una web app reale si userebbero i cookie di sessione o un DB locale)
SESSIONE_CLIENT = {
    "t_id": None,
    "firma_idp_s": None,
    "sk_studente": None,
    "pk_studente": None,  
    "seq_voto": 0
}

@app.route('/')
def home():
    """Carica l'interfaccia grafica (index.html)"""
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    """Riceve i dati dal frontend web e contatta l'IdP"""
    dati = request.json
    matricola = dati.get('matricola')
    totp_code = dati.get('totp')

    try:
        # Contattiamo il server OIDC dell'Ateneo
        response = requests.post(IDP_URL, json={"client_id": matricola, "totp_code": totp_code}, verify=False)
        
        if response.status_code == 200:
            token_data = response.json()
            
            # Salviamo i token anonimi nella "sessione"
            SESSIONE_CLIENT["t_id"] = token_data["id_token"]
            SESSIONE_CLIENT["firma_idp_s"] = token_data["access_token"]
            
            # Generiamo le chiavi effimere RSA dello studente per questa sessione di voto
            sk_studente, pk_studente = CryptoUtils.generate_rsa_keypair()
            SESSIONE_CLIENT["sk_studente"] = sk_studente
            SESSIONE_CLIENT["pk_studente"] = pk_studente
            
            return jsonify({"status": "success", "message": "Autenticazione OIDC riuscita. Identità verificata."})
        else:
            return jsonify({"status": "error", "message": "Credenziali o codice TOTP errati o Token già emesso."}), response.status_code
            
    except requests.exceptions.RequestException:
        return jsonify({"status": "error", "message": "Impossibile connettersi all'IdP d'Ateneo. Assicurati che server_oidc.py sia in esecuzione."}), 500

@app.route('/api/vote', methods=['POST'])
def esegui_voto():
    """Cifra il voto ed esegue la transazione su Blockchain"""
    dati = request.json
    preferenze = dati.get('preferenze')

    # Recupero i token e le chiavi dalla sessione utente
    t_id = SESSIONE_CLIENT.get("t_id")
    firma_idp_s = SESSIONE_CLIENT.get("firma_idp_s")
    sk_studente = SESSIONE_CLIENT.get("sk_studente")
    pk_studente = SESSIONE_CLIENT.get("pk_studente")

    if not t_id:
        return jsonify({"status": "error", "message": "Utente non autenticato. Effettua prima il login."}), 401

    try:
        # --- 1. CRITTOGRAFIA (OAEP e PSS) ---
        # Per la simulazione generiamo al volo la chiave pubblica della commissione
        # (Nel mondo reale, questa chiave è pubblica, fissa e distribuita a priori)
        _, pk_comm = CryptoUtils.generate_rsa_keypair()
        
        # Cifratura stocastica OAEP del payload del voto
        c_cifrato = CryptoUtils.rsa_encrypt_oaep(pk_comm, preferenze)
        
        t_vote = int(time.time())
        SESSIONE_CLIENT["seq_voto"] += 1
        seq_voto = SESSIONE_CLIENT["seq_voto"]
    
        # Creiamo il pacchetto da firmare e lo firmiamo con PSS
        msg_studente = f"{c_cifrato}||{t_vote}||{seq_voto}||{firma_idp_s}"
        sigma_studente = CryptoUtils.rsa_sign_pss(sk_studente, msg_studente)
        pk_studente_pem = CryptoUtils.export_public_key(pk_studente)

        # --- 2. SOTTOMISSIONE WEB3 A GANACHE ---
        w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
        if not w3.is_connected():
            raise Exception("Impossibile connettersi a Ganache sulla porta 7545.")
            
        w3.eth.default_account = w3.eth.accounts[0]

        # Caricamento ABI e Indirizzo del Contratto
        with open("../contracts/abi.json", "r") as f:
            abi = json.load(f)
        
        with open("../contract_address.txt", "r") as f:
            CONTRACT_ADDRESS = f.read().strip()

        urna_contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
        
        # Invocazione della funzione sottomettiVoto dello Smart Contract
        tx_hash = urna_contract.functions.sottomettiVoto(
            t_id, c_cifrato, sigma_studente, t_vote, seq_voto, pk_studente_pem
        ).transact()
        
        # Attendiamo la conferma dell'inserimento nel blocco
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        # Restituiamo i dati al frontend per mostrare la ricevuta
        return jsonify({
            "status": "success",
            "block": receipt.blockNumber,
            "gas": receipt.gasUsed,
            "tx_hash": tx_hash.hex()
        })

    except Exception as e:
        print(f"Errore durante l'invio del voto: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/totp', methods=['GET'])
def get_totp_demo():
    """API dedicata SOLO alla demo visiva: simula l'app Authenticator dello studente"""
    import time
    # Usiamo il segreto hardcoded della matricola MAT_001 per la demo
    segreto_mfa = b"SEGRETO_MFA_MARIO_2026"
    codice = CryptoUtils.generate_totp(segreto_mfa)
    secondi_rimanenti = 30 - (int(time.time()) % 30)
    
    return jsonify({
        "totp": codice,
        "expires_in": secondi_rimanenti
    })

if __name__ == '__main__':
    print("================================================================")
    print(" AVVIO CABINA ELETTORALE WEB")
    print("================================================================")
    print("Vai su http://localhost:8080 per accedere all'interfaccia.")
    # Eseguiamo il server sulla porta 8080 per non sovrapporci all'IdP
    app.run(port=8080, debug=True)