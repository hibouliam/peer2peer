import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa
import os
import json
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature
import base64
import socket

def compute_pow(key: str, difficulty: int = 4) -> int:
    """
    Trouve un nonce pour que hash(key + nonce) commence par un certain nombre de zéros.
    """
    nonce = 0
    prefix = "0" * difficulty
    while True:
        hash_attempt = hashlib.sha256(f"{key}{nonce}".encode()).hexdigest()
        if hash_attempt.startswith(prefix):
            return nonce
        nonce += 1

# def verify_pow(key: str, nonce: int, difficulty: int = 4) -> bool:
#     """
#     Vérifie si le nonce fourni est valide pour la clé donnée.
#     """
#     prefix = "0" * difficulty
#     hash_value = hashlib.sha256(f"{key}{nonce}".encode()).hexdigest()
#     return hash_value.startswith(prefix)


# def request_pow_verification(peers, key, nonce, difficulty=4):
#     """
#     Demande aux pairs voisins de vérifier la validité du PoW.
#     """
#     print(f"Demande de vérification PoW : key = {key}, nonce = {nonce}, difficulty = {difficulty}")
    
#     valid_count = 0
#     required_validations = max(1, len(peers) // 2)  # On demande validation à la majorité des pairs

#     for peer in peers:
#         try:
#             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#                 s.connect((peer["ip"], peer["port"]))
#                 request = json.dumps({"action": "verify_pow", "key": key, "nonce": nonce, "difficulty": difficulty})
#                 s.sendall(request.encode())
                
#                 response = json.loads(s.recv(1024).decode())
#                 if response.get("valid"):
#                     valid_count += 1
                
#                 print(f"Réponse reçue de {peer['ip']}:{peer['port']} - valid : {response.get('valid')}")

#                 if valid_count >= required_validations:
#                     return True  # Le PoW est validé par assez de pairs
#         except Exception as e:
#             print(f"Erreur lors de la communication avec {peer['ip']}:{peer['port']} - {e}")

#     return False  # PoW non validé par assez de pairs




def generate_key_pair():
    """
    Génère une paire de clés publique/privée RSA
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    # Sérialisation des clés pour stockage
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem


def sign_message(message: dict, private_key_pem):
    """
    Signe un message avec la clé privée du pair
    """
    #print(f"🔹 Données AVANT signature : {message}")  # Ajout ici

    private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    message_bytes = json.dumps(message).encode('utf-8')

    signature = private_key.sign(
        message_bytes,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    
    return signature


def verify_message_signature(message: dict, signature: bytes, public_key_pem):
    """
    Vérifie la signature d'un message en utilisant la clé publique de l'expéditeur
    """
    print(f"🔹 Clé publique utilisée pour vérifier : {public_key_pem}")

    public_key = serialization.load_pem_public_key(public_key_pem)
    message_bytes = json.dumps(message).encode('utf-8')

    try:
        public_key.verify(
            signature,
            message_bytes,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        print("Signature vérifiée avec succès.")
        return True
    except InvalidSignature:
        print("Échec de la vérification de la signature.")
        return False
