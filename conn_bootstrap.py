import socket
import threading
import json
import sys
from recup_ip import generate_key
import msgpack
from dht import assign_dht, request_dht,handle_dht, send_dht_local,create_signed_message, create_message
from security import generate_key_pair

BOOTSTRAP_HOST = '127.0.0.1'  # Adresse du serveur bootstrap
BOOTSTRAP_PORT = 5001     # Port du bootstrap
PEER_PORT = 7011     # Port d'écoute du pair

active_peers = []  # Liste des pairs actifs

my_node=[generate_key(f'127.0.0.1:{PEER_PORT}'),'127.0.0.1',PEER_PORT]
dht_local = {}

private_key, public_key = generate_key_pair()

def bootstrap_interaction(action :str, active_peers : list) -> None : 
    """
    Fonction unique pour interagir avec le serveur Bootstrap pour se connecter (JOIN) ou quitter le réseau (LEAVE).

    Paramètre :
    - action : 'JOIN' pour se connecter au réseau ou 'LEAVE' pour le quitter.
    """
    if action not in ['JOIN', 'LEAVE']:
        print("Action non valide. Utilisez 'JOIN' ou 'LEAVE'.")
        return

    try:
        global dht_local
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
                #global active_peers
                active_peers = json.loads(response)  # Stockage des pairs actifs
                return active_peers
            

            elif action == "LEAVE":
                response = s.recv(1024).decode('utf-8') # Réception du message envoyé par le bootstrap
                attempt_peer_connections(my_node)
                active_peers = sorted(active_peers, key=lambda peer: int(peer[0], 16))
                print(response)  # Afficher le message "Send your port for LEAVE"
                s.sendall(str(PEER_PORT).encode('utf-8'))  # Envoi du port d'écoute
                
                response = s.recv(1024).decode('utf-8')
                if responsability_plage[1] == None :
                    dht_local = send_dht_local(dht_local,active_peers[1],responsability_plage[0],responsability_plage[1], private_key)
                else :
                    dht_local = send_dht_local(dht_local,active_peers[0],responsability_plage[0],responsability_plage[1], private_key)
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
        global dht_local
        global responsability_plage

        # 🔹 Réception des données en plusieurs morceaux
        chunks = []
        while True:
            chunk = conn.recv(1024)
            if not chunk:
                break  # 🔹 Fin de la transmission
            chunks.append(chunk)

        full_data = b"".join(chunks)  # 🔹 Reconstruction complète du message

        if not full_data:
            print("❌ Aucune donnée reçue, connexion fermée par le pair distant")
            return  # Sortie de la fonction

        print(f"📥 Données brutes reçues ({len(full_data)} octets) : {full_data[:200]}...")  # 🔹 Affichage des premiers caractères pour debug

        data = msgpack.unpackb(full_data) 

        if data.get("action") == "Connection with the peer" :
            add_neighbor_peer(data, my_node, active_peers)
        
        # elif data.get("action") == "verify_pow":
        #     # 🔹 Vérification de la preuve de travail demandée par un pair
        #     key = data.get("key")
        #     nonce = data.get("nonce")
        #     difficulty = data.get("difficulty", 4)  # Valeur par défaut

        #     is_valid = verify_pow(key, nonce, difficulty)

        #     # 🔹 Envoi de la réponse au pair demandeur
        #     response = msgpack.packb({"valid": is_valid})
        #     conn.sendall(response)
        #     print(f"🔎 PoW vérifié : {'✅ Valide' if is_valid else '❌ Invalide'}")

        else :
            dht_local = handle_dht(my_node,active_peers,data, dht_local, responsability_plage, private_key)
            responsability_plage = assign_dht(my_node, active_peers)
            return dht_local
        
    except Exception as e:
        print(f"Peer management error : {e}")
    finally:
        conn.close() # Fermeture de la connexion
        

def attempt_peer_connections(my_node : list):
    """
    Tentative de connexion à chaque pairs actifs
    """
    #global my_node
    if len(active_peers) < 1 :    
        return  # Exit the function if only one peer exists
    else :
        for peer in active_peers:
            peer_ip, peer_port = peer[1:]
            try:                
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((peer_ip, peer_port)) # connexion au pair
                    message = {"action": "Connection with the peer", "data": [my_node, active_peers]}
                    message = create_signed_message(message, private_key)  # 🔹 Ajoute la signature
                    s.sendall(msgpack.packb(message))
            except Exception as e:
                print(f"Peer connection error {peer_ip}:{peer_port} : {e}")


def add_neighbor_peer(data: str, my_node : list, active_peers:list) -> None:
    """
    Ajoute un pair voisin à la liste active_peers_neighbor si le message reçu correspond au format attendu.

    Paramètres :
    - data : Le message reçu sous forme de chaîne de caractères.

    Actions :
    - Si le message contient "Successful connection with the peer {JSON}", extrait l'IP et le port et les ajoute.
    """
    #global my_node
    #global active_peers
    #global responsability_plage
    try:
        if data.get("action") == "Connection with the peer":
            peer_info = data["data"]
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
                                return 
                        else :
                            active_peers.append(peer) 
           
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
        print("3. Tapez 'a' pour ajouter un fichier")
        print("4. Tapez 'p' pour afficher les données du noeud")
        action = input("Votre choix : ").lower()

        if action == 'j':
            active_peers = bootstrap_interaction("JOIN", active_peers)  # Tester l'action JOIN
            server_thread = threading.Thread(target=start_peer_server) # Création d'un thread pour gérer la connexion entre 2 pairs avec la fonction start_peer_server
            server_thread.daemon = True
            server_thread.start()
            # Se connecter aux autres pairs du réseau
            attempt_peer_connections(my_node)
            responsability_plage=assign_dht(my_node, active_peers)

            request_dht(my_node, active_peers, responsability_plage, private_key)
            

        elif action == 'q':
            bootstrap_interaction("LEAVE", active_peers)  # Tester l'action LEAVE
            break  # Sortie de la boucle après avoir quitté le réseau
        elif action == 'a' :
            fichier = "main.py"
            fichier_coder = create_message(fichier, my_node, private_key, public_key)
            data = {"action":"add_file", "data": fichier_coder}
            dht_local=handle_dht(my_node, active_peers, data, dht_local, responsability_plage, private_key)
        elif action == 'p':
            print("Plage de responsabilité :", responsability_plage)
            print("Liste des pairs actifs :", active_peers)
            print("dht local :",dht_local)
        else:
            print("Choix non valide. Veuillez taper 'j' ou 'q'.")
            
except KeyboardInterrupt:
    print("\nInterruption par l'utilisateur. Déconnexion en cours...")
    bootstrap_interaction("LEAVE", active_peers)
