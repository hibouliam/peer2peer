import socket
import threading
import json
from recup_ip import generate_key


HOST = '127.0.0.1'  # Adresse du serveur bootstrap
PORT = 5001      # Port d'écoute du bootstrap

active_peers = []     # Liste des pairs actifs


def process_peer_connection(conn, addr):
    """
    Gestion de la connexion d'un nouveau pair coté Bootstrap, qui l'ajoute à la liste des pairs actifs et envoie 
    la liste au pair pour qu'il puisse se connecter à eux.

    2 paramètres : 
    conn : l'objet de connexion qui permet d'envoyer et recevoir des données via le socket.
    addr : une paire (IP, port) qui représente l'adresse de l'ordinateur connecté   
    """
    try:
        # Réception de la commande initiale (JOIN ou LEAVE)
        action = conn.recv(1024).decode('utf-8').strip()
        
        if action == 'JOIN':
            print(f"New connected peer information : {addr}") # Attribution automatiquement un port source temporaire et unique pour cette connexion
            conn.sendall("Send your listening port".encode('utf-8'))  # Demande du port d'écoute
            port_data = conn.recv(1024).decode('utf-8').strip()  # Réception du port
            print(f"Peer listening port : {port_data}")
            
            new_peer = (generate_key(addr[0]),addr[0], int(port_data))
            if new_peer not in active_peers:
                active_peers.append(new_peer) # Ajout du pair à la liste des pairs actifs
                active_peers = sorted(active_peers,key=lambda peer: int(peer[0], 16)) # Remet en entier base 16
                new_peer_index = active_peers.index(new_peer)
                print(f"Pair ajouté : {new_peer}")
                print("Liste des pairs actifs :", active_peers)
                if len (active_peers)==1 :
                    conn.sendall(json.dumps([]).encode('utf-8'))
                if len(active_peers)==2 :
                    neighbor_index=(new_peer_index+1)%len(active_peers)
                    neighbor=active_peers[neighbor_index]
                    conn.sendall(json.dumps([neighbor]).encode('utf-8'))
                if len(active_peers)>=3 :
                    left_neighbor_index=(new_peer_index-1)%len(active_peers)  #modulo pour retourner a 1
                    right_neighbor_index=(new_peer_index+1)%len(active_peers)  
                    left_neighbor=active_peers[left_neighbor_index]
                    right_neighbor=active_peers[right_neighbor_index]
                    print("Liste des pairs actif :", left_neighbor,right_neighbor)
                    conn.sendall(json.dumps([left_neighbor,right_neighbor]).encode('utf-8'))

        elif action == 'LEAVE':
            print(f"Le pair {addr} demande à quitter le réseau.")
            conn.sendall("Send your port for LEAVE".encode('utf-8'))  # Demande du port pour quitter le réseau
            
            port_data = conn.recv(1024).decode('utf-8').strip()  # Réception du port
            print(f"Port reçu pour LEAVE : {port_data}")
            
            peer_to_remove = (generate_key(addr[0]),addr[0], int(port_data))
            if peer_to_remove in active_peers:
                active_peers.remove(peer_to_remove) # Suppresion du pair de la liste des pairs actifs
                print(f"Pair supprimé : {peer_to_remove}")
                conn.sendall("Successfully removed from network".encode('utf-8')) # Envoi du message au pair
                print("Liste des pairs actifs :", active_peers)
                
            else:
                print(f"Pair non trouvé : {peer_to_remove}")
                conn.sendall("Peer not found in the active list".encode('utf-8'))
        else:
            print(f"Commande inconnue reçue : {action}")

    except Exception as e:
        print(f"Erreur lors du traitement de la connexion avec {addr} : {e}")

    finally:
        conn.close()  # Fermeture de la connexion



def start_bootstrap_server():
    """
    Activation du serveur Bootstrap pour accepter la connexion de nouveaux pairs au réseau.
    """

    # Création d'un objet socket pour la communication réseau.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # socket.AF_INET : utilisation du protocole IPv4 & socket.SOCK_STREAM : TCP (Transmission Control Protocol)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Définition des paramètres
    server_socket.bind((HOST, PORT)) # Associe l'adresse IP (HOST) et le numéro de port (PORT) au socket
    server_socket.listen(5) # Socket en mode écoute pour les connexions entrantes
    print(f"Bootstrap server started on {HOST}:{PORT}")
    
    while True:
        conn, addr = server_socket.accept() # Accepte et écoute des connexions entrantes 
        thread = threading.Thread(target=process_peer_connection, args=(conn, addr)) # Création d'un thread pour gérer chaque connexion entrante d'un pair au Bootstrap avec la fonction handle_peer
        thread.start() # Lance le thread pour traiter la connexion en parallèle.

if __name__ == "__main__":
    start_bootstrap_server()