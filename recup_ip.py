import socket
import hashlib

def generate_key(filename: str) -> str:
    """Génère une clé unique pour un fichier en utilisant SHA."""
    return hashlib.sha3_512(filename.encode()).hexdigest()

def get_local_ip() -> str:
    try:
        # Crée une connexion UDP temporaire pour déterminer l'IP locale
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Utilise une IP externe pour déterminer l'IP locale
            local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "Impossible de récupérer l'adresse IP locale"
    return local_ip

def get_free_tcp_port():
    # Crée une socket TCP et demande un port libre
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))  # "" pour écouter sur toutes les interfaces
        free_port = s.getsockname()[1]  # Récupère le port alloué dynamiquement
    return free_port

# Utilisation
local_ip = get_local_ip()
tcp_port = get_free_tcp_port()
