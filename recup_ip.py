import socket
import requests

def get_public_ip():
    try:
        # Envoie une requête à un service de récupération de l'IP publique
        response = requests.get("https://api64.ipify.org?format=json")
        response.raise_for_status()  # Vérifie les erreurs HTTP
        ip = response.json()["ip"]
    except requests.RequestException:
        ip = "Impossible de récupérer l'adresse IP publique"
    return ip

def get_free_tcp_port():
    # Crée une socket TCP et demande un port libre
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))  # "" pour écouter sur toutes les interfaces
        free_port = s.getsockname()[1]  # Récupère le port alloué dynamiquement
    return free_port

# Utilisation
public_ip = get_public_ip()
tcp_port = get_free_tcp_port()
print(f"Adresse IP publique : {public_ip}")
print(f"Port TCP libre : {tcp_port}")
