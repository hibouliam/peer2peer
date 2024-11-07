import socket
import threading
import json

HOST = '0.0.0.0'  # Adresse du serveur bootstrap
PORT = 5000        # Port d'écoute du bootstrap

peers_list = []     # Liste des pairs actifs

def handle_peer(conn, addr):
    """
    Gère la connexion d'un pair et envoie la liste des autres pairs.
    """
    data = conn.recv(1024).decode('utf-8')  # Lecture de la demande d'inscription
    if data == 'JOIN':
        print(f"Nouveau pair connecté : {addr}")
        # Demander au pair d'envoyer son port d'écoute
        conn.sendall("Send your listening port".encode('utf-8'))
        port_data = conn.recv(1024).decode('utf-8')  # Recevoir le port d'écoute du pair
        print(f"Pair a envoyé son port d'écoute : {port_data}")
        
        # Ajouter le pair à la liste des pairs actifs
        peers_list.append((addr[0], int(port_data)))
        
        # Envoi de la liste des pairs aux autres
        conn.sendall(json.dumps(peers_list).encode('utf-8'))
    
    conn.close()

def start_bootstrap_server():
    """
    Lance le serveur bootstrap pour accepter les pairs entrants.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Serveur bootstrap démarré sur {HOST}:{PORT}")
    
    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_peer, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_bootstrap_server()
