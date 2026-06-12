import time
import hmac
import hashlib
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization

class CryptoUtils:
    # --- FUNZIONI TOTP (Lab 01/07) ---
    @staticmethod
    def generate_totp(secret_key: bytes, interval_x: int = 30) -> str:
        current_time = int(time.time())
        t = current_time // interval_x
        t_bytes = t.to_bytes(8, byteorder='big')
        hmac_digest = hmac.new(secret_key, t_bytes, hashlib.sha256).digest()
        offset = hmac_digest[-1] & 0x0F
        binary = ((hmac_digest[offset] & 0x7F) << 24 |
                  (hmac_digest[offset+1] & 0xFF) << 16 |
                  (hmac_digest[offset+2] & 0xFF) << 8 |
                  (hmac_digest[offset+3] & 0xFF))
        totp = binary % 10**6
        return f"{totp:06d}"

    # --- FUNZIONI RSA (Lab 02) ---
    @staticmethod
    def generate_rsa_keypair():
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def export_public_key(public_key) -> str:
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')

    @staticmethod
    def rsa_sign_pss(private_key, message: str) -> str:
        signature = private_key.sign(
            message.encode('utf-8'),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')

    @staticmethod
    def rsa_encrypt_oaep(public_key, message: str) -> str:
        ciphertext = public_key.encrypt(
            message.encode('utf-8'),
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
        return base64.b64encode(ciphertext).decode('utf-8')