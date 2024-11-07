import socket
import threading
import json

BOOTSTRAP_HOST = '127.0.0.1'  # Adresse du serveur bootstrap
BOOTSTRAP_PORT = 5000         # Port du bootstrap
PEER_PORT = 7000              # Port d'écoute du pair

active_peers = []  # Liste des pairs actifs

def connect_to_bootstrap():
    """
    Connecte le pair au serveur bootstrap et obtient la liste des autres pairs.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((BOOTSTRAP_HOST, BOOTSTRAP_PORT))
            s.sendall("JOIN".encode('utf-8'))  # Envoi de la demande d'inscription
            response = s.recv(1024).decode('utf-8')
            print(response)  # Afficher le message du serveur bootstrap
            if response == "Send your listening port":
                s.sendall(str(PEER_PORT).encode('utf-8'))  # Envoyer le port d'écoute du pair
            response = s.recv(1024).decode('utf-8')
            global active_peers
            active_peers = json.loads(response)  # Stockage des pairs actifs
            print("Liste des pairs reçue du bootstrap:", active_peers)
    except Exception as e:
        print(f"Erreur de connexion au bootstrap : {e}")

def start_peer_server():
    """
    Lance le serveur pair pour écouter les connexions entrantes.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', PEER_PORT))  # Bind sur un port spécifique
    server_socket.listen(5)
    print(f"Serveur pair démarré, en écoute sur le port {PEER_PORT}")
    
    while True:
        conn, addr = server_socket.accept()
        print(f"Connexion entrante de {addr}")
        handle_peer(conn)

def handle_peer(conn):
    """
    Gère la communication avec un pair entrant.
    """
    try:
        data = conn.recv(1024).decode('utf-8')
        print(f"Reçu du pair : {data}")
        # Traitement des données ici
    except Exception as e:
        print(f"Erreur de gestion de pair : {e}")
    finally:
        conn.close()

def listen_for_new_peers():
    """
    Écoute en permanence la liste des pairs pour se connecter à eux.
    """
    for peer in active_peers:
        peer_ip, peer_port = peer
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((peer_ip, peer_port))
                s.sendall("Hello from new peer!".encode('utf-8'))
                print(f"Connexion réussie avec le pair {peer}")
        except Exception as e:
            print(f"Erreur de connexion au pair {peer_ip}:{peer_port} : {e}")

# Démarrer le serveur et la connexion au bootstrap
server_thread = threading.Thread(target=start_peer_server)
server_thread.daemon = True
server_thread.start()

# Connecter au bootstrap
connect_to_bootstrap()

# Se connecter aux autres pairs du réseau
listen_for_new_peers()

print("Le pair est maintenant actif et écoute les nouvelles connexions.")

while True:
    pass