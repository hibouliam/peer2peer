import socket
import threading
import json
import sys

BOOTSTRAP_HOST = '0.0.0.0'  # Adresse du serveur bootstrap
BOOTSTRAP_PORT = 5010         # Port du bootstrap
PEER_PORT = 7001             # Port d'écoute du pair

active_peers = []  # Liste des pairs actifs

# def connect_to_bootstrap():
#     """
#     Connexion au serveur Bootstrap coté pair
#     """
#     try:
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # socket.AF_INET : utilisation du protocole IPv4 & socket.SOCK_STREAM : TCP (Transmission Control Protocol)
#             s.connect((BOOTSTRAP_HOST, BOOTSTRAP_PORT)) # Connexion avec le serveur bootstrap
#             s.sendall("JOIN".encode('utf-8'))  # Envoi de la demande d'inscription
#             response = s.recv(1024).decode('utf-8') # Attente de la réponse du bootstrap
#             print(response)  # Afficher le message du serveur bootstrap
#             if response == "Send your listening port":
#                 s.sendall(str(PEER_PORT).encode('utf-8'))  # Envoie du port d'écoute du pair
#             response = s.recv(1024).decode('utf-8') # Attente de la réponse du bootstrap
#             global active_peers
#             active_peers = json.loads(response)  # Stockage des pairs actifs
#             print("List of active peers:", active_peers)
#     except Exception as e:
#         print(f"Bootstrap connection error : {e}")


# def leave_network():
#     """
#     Fonction pour quitter proprement le réseau en informant le serveur bootstrap.
#     """
#     try:
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#             s.connect((BOOTSTRAP_HOST, BOOTSTRAP_PORT))
#             s.sendall("LEAVE".encode('utf-8'))  # Informer le bootstrap du départ
#             s.sendall(str(PEER_PORT).encode('utf-8'))  # Envoi du port d'écoute du pair pour identification
#             response = s.recv(1024).decode('utf-8')
#             if response == "OK":
#                 print("Vous avez quitté le réseau avec succès.")
#             else:
#                 print("Erreur lors de la tentative de quitter le réseau.")
#     except Exception as e:
#         print(f"Erreur lors de la déconnexion du réseau : {e}")
#     finally:
#         sys.exit()  # Fermer le programme proprement


def bootstrap_interaction(action):
    """
    Fonction unique pour interagir avec le serveur Bootstrap pour se connecter (JOIN) ou quitter le réseau (LEAVE).

    Paramètre :
    - action : 'JOIN' pour se connecter au réseau ou 'LEAVE' pour le quitter.
    """
    if action not in ['JOIN', 'LEAVE']:
        print("Action non valide. Utilisez 'JOIN' ou 'LEAVE'.")
        return

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((BOOTSTRAP_HOST, BOOTSTRAP_PORT))
            s.sendall(action.encode('utf-8'))  # Envoi de l'action ('JOIN' ou 'LEAVE')

            if action == "JOIN":
                response = s.recv(1024).decode('utf-8')
                print(response)  # Afficher le message du serveur bootstrap
                if response == "Send your listening port":
                    s.sendall(str(PEER_PORT).encode('utf-8'))  # Envoi du port d'écoute du pair

                # Récupérer la liste des pairs actifs
                response = s.recv(1024).decode('utf-8')
                global active_peers
                active_peers = json.loads(response)  # Stockage des pairs actifs
                print("Liste des pairs actifs :", active_peers)

            elif action == "LEAVE":
                response = s.recv(1024).decode('utf-8')
                print(response)  # Afficher le message "Send your port for LEAVE"
                s.sendall(str(PEER_PORT).encode('utf-8'))  # Envoi du port d'écoute
                
                response = s.recv(1024).decode('utf-8')
                print(f"Réponse reçue du Bootstrap : {response}")

    except Exception as e:
        print(f"Erreur lors de l'interaction avec le Bootstrap ({action}) : {e}")

    if action == "LEAVE":
        sys.exit()  # Fermer le programme proprement après la déconnexion


def start_peer_server():
    """
    Lance un serveur destiné à accepter/gèrer les connexions entre pairs déjà connectés au réseau
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', PEER_PORT))  # Accepte les connexions de n'importe quelle interface réseau de la machine
    server_socket.listen(5)
    print(f"Peer server started, listening on port {PEER_PORT}")
    
    while True:
        conn, addr = server_socket.accept()
        print(f"Incoming connection from {addr}")
        handle_communication_between_peer(conn)



def handle_communication_between_peer(conn):
    """
    Gère la communication entre 2 pairs. Ici, réception et affichage des données envoyées
    """
    try:
        data = conn.recv(1024).decode('utf-8') # Attente, réception et décodage des données
        print(f"Received data : {data}") 
        # Traitement des données ici
    except Exception as e:
        print(f"Peer management error : {e}")
    finally:
        conn.close() # Fermeture de la connexion



def attempt_peer_connections():
    """
    Tentative de connexion à chaque pairs actifs
    """
    for peer in active_peers:
        peer_ip, peer_port = peer
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((peer_ip, peer_port)) # connexion au pair
                s.sendall("Hello new peer!".encode('utf-8'))
                print(f"Successful connection with the peer {peer}")
        except Exception as e:
            print(f"Peer connection error {peer_ip}:{peer_port} : {e}")

server_thread = threading.Thread(target=start_peer_server) # Création d'un thread pour gérer la connexion entre 2 pairs avec la fonction start_peer_server
server_thread.daemon = True
server_thread.start()


# Connecter au bootstrap
#connect_to_bootstrap()
#bootstrap_interaction("JOIN")

# Se connecter aux autres pairs du réseau
attempt_peer_connections()

print("Le pair est maintenant actif et écoute les nouvelles connexions.")

# try : 
#     while True:
#         action = input("Tapez 'q' pour quitter le réseau : ")
#         if action.lower() == 'q':
#             leave_network()
# except KeyboardInterrupt:
#     print("\nInterruption par l'utilisateur. Déconnexion en cours...")
#     leave_network()

# Tester l'interaction avec le bootstrap
try:
    while True:
        print("\nActions disponibles :")
        print("1. Tapez 'j' pour rejoindre le réseau.")
        print("2. Tapez 'q' pour quitter le réseau.")
        
        action = input("Votre choix : ").lower()

        if action == 'j':
            bootstrap_interaction("JOIN")  # Tester l'action JOIN
        elif action == 'q':
            bootstrap_interaction("LEAVE")  # Tester l'action LEAVE
            break  # Sortie de la boucle après avoir quitté le réseau
        else:
            print("Choix non valide. Veuillez taper 'j' ou 'q'.")
            
except KeyboardInterrupt:
    print("\nInterruption par l'utilisateur. Déconnexion en cours...")
    bootstrap_interaction("LEAVE")
