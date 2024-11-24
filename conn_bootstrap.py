import socket
import threading
import json
import sys
from recup_ip import generate_key


BOOTSTRAP_HOST = '127.0.0.1'  # Adresse du serveur bootstrap
BOOTSTRAP_PORT = 5001     # Port du bootstrap
PEER_PORT = 7004         # Port d'écoute du pair

active_peers = []  # Liste des pairs actifs

peer=[]


def bootstrap_interaction(action :str) -> None : 
    """
    Fonction unique pour interagir avec le serveur Bootstrap pour se connecter (JOIN) ou quitter le réseau (LEAVE).

    Paramètre :
    - action : 'JOIN' pour se connecter au réseau ou 'LEAVE' pour le quitter.
    """
    if action not in ['JOIN', 'LEAVE']:
        print("Action non valide. Utilisez 'JOIN' ou 'LEAVE'.")
        return

    try:
        # Création d'un objet socket pour la communication réseau.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # socket.AF_INET : utilisation du protocole IPv4 & socket.SOCK_STREAM : TCP (Transmission Control Protocol)
            s.connect((BOOTSTRAP_HOST, BOOTSTRAP_PORT)) # Connexion au bootstrap
            s.sendall(action.encode('utf-8'))  # Envoi de l'action ('JOIN' ou 'LEAVE')

            if action == "JOIN":
                response = s.recv(1024).decode('utf-8') # Réception du message envoyé par le bootstrap
                print(response)  # Afficher le message du serveur bootstrap
                if response == "Send your listening port":
                    s.sendall(str(PEER_PORT).encode('utf-8'))  # Envoi du port d'écoute du pair

                # Récupérer la liste des pairs actifs
                response = s.recv(1024).decode('utf-8') # Réception du message envoyé par le bootstrap
                global active_peers
                active_peers = json.loads(response)  # Stockage des pairs actifs
                print("Liste des pairs actifs :", active_peers)

            elif action == "LEAVE":
                response = s.recv(1024).decode('utf-8') # Réception du message envoyé par le bootstrap
                attempt_peer_connections()
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
    # Création d'un objet socket pour la communication réseau.
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
        add_neighbor_peer(data)
        print(type(data))
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
    global peer
    if len(active_peers) < 1 :    
        return  # Exit the function if only one peer exists
    else :
        for peer in active_peers:
            peer_ip, peer_port = peer[1:]
            try:                
                peer = [generate_key(f'127.0.0.1:{PEER_PORT}'),'127.0.0.1',PEER_PORT]
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((peer_ip, peer_port)) # connexion au pair
                    s.sendall(f"Successful connection with the peer {[peer,active_peers]}".encode('utf-8'))
            except Exception as e:
                print(f"Peer connection error {peer_ip}:{peer_port} : {e}")


def add_neighbor_peer(data: str) -> None:
    """
    Ajoute un pair voisin à la liste active_peers_neighbor si le message reçu correspond au format attendu.

    Paramètres :
    - data : Le message reçu sous forme de chaîne de caractères.

    Actions :
    - Si le message contient "Successful connection with the peer {JSON}", extrait l'IP et le port et les ajoute.
    """
    global active_peers
    try:
        if data.startswith("Successful connection with the peer "):
            # Extrait la partie JSON du message
            peer_info_str = data[len("Successful connection with the peer "):].strip()
            peer_info_str = peer_info_str.replace("'", '"')
            peer_info = json.loads(peer_info_str)  # Convertit le JSON en liste [IP, PORT]
            peer_info = applatir_données(peer_info)
            
            if len(active_peers)<=1 :
                active_peers.append(peer_info[0])
            else :
                count=0 #Pour ne pas enlever plus de deux peer
                for peer in peer_info :
                    if peer[1:] !=['127.0.0.1',PEER_PORT]:
                        if peer in active_peers  :
                            if count == 0 :
                                count +=1 
                                active_peers.remove(peer) 
                            else :
                                print(f"les actives paires {active_peers}")
                                return 
                        else :
                            active_peers.append(peer) 
                        
            print(f"les actives paires sont {active_peers}")
                
    except Exception as e:
        print(f"Erreur lors de l'ajout d'un pair voisin : {e}")

def applatir_données(data :list)-> list :
    result=[]
    for item in data:
        if isinstance(item[0], list):  # Vérifie si c'est un sous-élément à aplatir
            result.extend(item)  # Ajoute chaque sous-élément directement
        else:
            result.append(item)  # Sinon, ajoute l'élément directement
    return result
try:
    while True:
        print("\nActions disponibles :")
        print("1. Tapez 'j' pour rejoindre le réseau.")
        print("2. Tapez 'q' pour quitter le réseau.")
        
        action = input("Votre choix : ").lower()

        if action == 'j':
            bootstrap_interaction("JOIN")  # Tester l'action JOIN
            server_thread = threading.Thread(target=start_peer_server) # Création d'un thread pour gérer la connexion entre 2 pairs avec la fonction start_peer_server
            server_thread.daemon = True
            server_thread.start()
            # Se connecter aux autres pairs du réseau
            attempt_peer_connections()
            #Reste à faire
            print("Liste des pairs actifs :", active_peers)

            #Tester voir si ca fonctionne
            #Si ca fonctionne faut faire une fonction pour dire qu'il est responsable de la plage de lui à son voisin suivant
            #Faire deux exceptions : - si ces deux voisins sont plus grands alors il est reponsable de 0 au voisin le plus proche de lui (par exemple si 1 a comme voisin 2 et 5 alors il responsable de 0 à 2 )
                                   # - si ces deux voisins sont plus petits alors il est reponsable  de lui à +infini (par exemple si 5 a comme voisin 1 et 4 alors il est responable de 5 à +infini)
            #Et pour l'écriture de la dht je propose soit dictionnaire map (dht={"file1":["12 7.0.0.1:8000","127.0.0.1:5000"]})  
            #Ou alors directement dans un fichier json  / on peut regarder messagepack(facile) ou protocol buffer (dfficle mais plus sécurisé)
            #Perso je pense que peu importe lequel on utilise on pourra changer facilement pcq ca reste un peu la même chose

            #Ca c'est autre chose
            #Enregistrer l'adresse ip de deux paires (celui a qui il envoie et celui qui recoit le message)
            #Gerer les déconnexions en envoyant le peer suivant au noeud précédent 
            #Peut être faire un test toute les x secondes pour verifier la connexion
        elif action == 'q':
            bootstrap_interaction("LEAVE")  # Tester l'action LEAVE
            break  # Sortie de la boucle après avoir quitté le réseau
        else:
            print("Choix non valide. Veuillez taper 'j' ou 'q'.")
            
except KeyboardInterrupt:
    print("\nInterruption par l'utilisateur. Déconnexion en cours...")
    bootstrap_interaction("LEAVE")
