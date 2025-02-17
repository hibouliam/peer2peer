import hashlib

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