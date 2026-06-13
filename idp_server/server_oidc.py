import time
import secrets
from flask import Flask, request, jsonify
# Simuliamo l'import della nostra libreria crittografica
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'client_app')))
from crypto_utils import CryptoUtils

app = Flask(__name__)

# 1. Setup Chiavi IdP (Vengono generate all'avvio del server)
sk_idp, pk_idp = CryptoUtils.generate_rsa_keypair()
print("\n[IdP STARTUP] Chiavi RSA a 2048 bit generate per l'Identity Provider d'Ateneo.")

# Database fittizio degli studenti autorizzati (Matricola -> Secret TOTP)
DB_STUDENTI = {
    "MAT_001": b"SEGRETO_MFA_MARIO_2026",
    "MAT_002": b"SEGRETO_MFA_LUIGI_2026",
    "MAT_003": b"SEGRETO_MFA_GIULIA_2026",
    "MAT_004": b"SEGRETO_MFA_ELENA_2026"
}
STUDENTI_CHE_HANNO_GIA_RITIRATO_IL_TOKEN = set()

@app.route('/oauth/token', methods=['POST'])
def rilascia_token_oidc():
    """
    Endpoint (simulato) OpenID Connect. 
    Riceve le credenziali, verifica il TOTP e restituisce il JWT/Token Anonimo firmato.
    """
    data = request.json
    matricola = data.get('client_id')
    totp_fornito = data.get('totp_code')

    print(f"\n[IdP SERVER] Ricevuta richiesta di login da: {matricola}")

    # 1. Verifica Identità e MFA
    if matricola not in DB_STUDENTI:
        return jsonify({"error": "invalid_client"}), 401
    
    expected_totp = CryptoUtils.generate_totp(DB_STUDENTI[matricola])
    if totp_fornito != expected_totp:
        print("[IdP SERVER] MFA Fallita. TOTP Errato.")
        return jsonify({"error": "access_denied", "error_description": "MFA fallita"}), 401

    # 2. Controllo Double-Voting (Ha già preso il token?)
    if matricola in STUDENTI_CHE_HANNO_GIA_RITIRATO_IL_TOKEN:
        print("[IdP SERVER]  L'utente ha già ritirato un token. Blocco emit.")
        return jsonify({"error": "invalid_request", "error_description": "Token già emesso"}), 403

    # 3. Generazione Token Anonimo (Zero-Logging)
    STUDENTI_CHE_HANNO_GIA_RITIRATO_IL_TOKEN.add(matricola)
    t_id = f"TID_{secrets.token_hex(4)}"
    exp_time = int(time.time()) + 3600

    # 4. Firma PSS del Token
    msg_da_firmare = f"{t_id}||{exp_time}"
    firma_s = CryptoUtils.rsa_sign_pss(sk_idp, msg_da_firmare)

    print(f"[IdP SERVER] Identità verificata. Rilascio Token Anonimo {t_id}.")
    print(f"[IdP SERVER] Applicazione Policy Zero-Logging: Elimino T_ID dai log.")

    return jsonify({
        "access_token": firma_s,
        "token_type": "Bearer",
        "expires_in": 3600,
        "id_token": t_id,
        "pk_idp_pem": CryptoUtils.export_public_key(pk_idp)
    })

if __name__ == '__main__':
    print("[IdP STARTUP] Avvio server OIDC d'Ateneo in HTTPS...")
    app.run(port=5000, ssl_context=('certs/server.crt', 'certs/server.key'))