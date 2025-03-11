# import subprocess
# import os
# import sys

# def open_new_terminal_and_run_script(script_path):
#     if sys.platform == "win32":  # Pour Windows
#         # Ouvre un terminal (cmd ou PowerShell) et exécute le script
#         subprocess.Popen(["start", "cmd", "/K", f"python {script_path}"], shell=True)
#     else:  # Pour Linux/macOS
#         # Ouvre un nouveau terminal (gnome-terminal, xterm, etc.) et exécute le script
#         subprocess.Popen(["gnome-terminal", "--", "python3", script_path])

# if __name__ == "__main__":
#     # script_to_run = "hello_world.py"  # Remplace avec le chemin correct du script
#     open_new_terminal_and_run_script("conn_bootstrap.py")

import socket,random
import threading
import json
import sys
from recup_ip import generate_key
import msgpack
from dht import assign_dht, request_dht,handle_dht, send_dht_local,create_add_file_message, create_looking_file_message, request_list_peer_have_file, send_replica_message,create_delete_file_message
from file_share import request_files,handle_files
from file_emplacement import add_file_to_network
import time
import os
import sys
import shutil

BOOTSTRAP_HOST = '127.0.0.1'  # Adresse du serveur bootstrap
BOOTSTRAP_PORT = 5001     # Port du bootstrap
# PEER_PORT = int(sys.argv[1])      # Port d'écoute du pair

active_peers = []  # Liste des pairs actifs

# my_node=[generate_key(f'127.0.0.1:{PEER_PORT}'),'127.0.0.1',PEER_PORT]
dht_local = {}

def bootstrap_interaction(action :str, active_peers : list, peer_port : int) -> None : 
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
        # peer_port = random.randint(1024, 65535)
        my_node = [generate_key(f'127.0.0.1:{peer_port}'),'127.0.0.1',peer_port]
        # Création d'un objet socket pour la communication réseau.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # socket.AF_INET : utilisation du protocole IPv4 & socket.SOCK_STREAM : TCP (Transmission Control Protocol)
            s.connect((BOOTSTRAP_HOST, BOOTSTRAP_PORT)) # Connexion au bootstrap
            s.sendall(action.encode('utf-8'))  # Envoi de l'action ('JOIN' ou 'LEAVE')

            if action == "JOIN":
                response = s.recv(1024).decode('utf-8') # Réception du message envoyé par le bootstrap
                print(response)  # Afficher le message du serveur bootstrap
                if response == "Send your listening port":
                    s.sendall(str(peer_port).encode('utf-8'))  # Envoi du port d'écoute du pair

                # Récupérer la liste des pairs actifs
                response = s.recv(1024).decode('utf-8') # Réception du message envoyé par le bootstrap
                #global active_peers
                active_peers = json.loads(response)  # Stockage des pairs actifs
                if not os.path.exists(f'.storage{peer_port}'):
                    os.makedirs(f'.storage{peer_port}') 
                return active_peers,
            

            elif action == "LEAVE":
                response = s.recv(1024).decode('utf-8') # Réception du message envoyé par le bootstrap
                attempt_peer_connections(my_node)
                active_peers = sorted(active_peers, key=lambda peer: int(peer[0], 16))
                print(response)  # Afficher le message "Send your port for LEAVE"
                s.sendall(str(peer_port).encode('utf-8'))  # Envoi du port d'écoute
                
                response = s.recv(1024).decode('utf-8')
                if os.path.exists(f'.storage{peer_port}'):
                    for f in os.listdir(f'.storage{peer_port}'):
                        if os.path.isfile(os.path.join(f'.storage{peer_port}', f)):
                            key=os.path.splitext(f)[0]
                            data= create_delete_file_message(key,my_node)
                            print(active_peers[1],key)
                            send_replica_message(my_node,[active_peers[1]],key)
                            time.sleep(1)
                            message= {"action" : "delete_peer_dht", "data" : data}
                            dht_local=handle_dht(my_node,active_peers,message, dht_local, responsability_plage)


                if responsability_plage[1] == None :
                    dht_local = send_dht_local(dht_local,active_peers[1],responsability_plage[0],responsability_plage[1])
                else :
                    dht_local = send_dht_local(dht_local,active_peers[0],responsability_plage[0],responsability_plage[1])
                print(f"Réponse reçue du Bootstrap : {response}")
                shutil.rmtree(f'.storage{peer_port}')

    except Exception as e:
        print(f"Erreur lors de l'interaction avec le Bootstrap ({action}) : {e}")

    if action == "LEAVE":
        sys.exit()  # Fermer le programme proprement après la déconnexion


def start_peer_server(peer_port,my_node):
    """
    Lance un serveur destiné à accepter/gèrer les connexions entre pairs déjà connectés au réseau
    """
    # Création d'un objet socket pour la communication réseau.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', peer_port))  # Accepte les connexions de n'importe quelle interface réseau de la machine
    server_socket.listen(5)
    print(f"Peer server started, listening on port {peer_port}")
    
    while True:
        conn, addr = server_socket.accept()
        print(f"Incoming connection from {addr}")
        handle_communication_between_peer(conn,my_node,peer_port=peer_port)



def handle_communication_between_peer(conn,my_node,peer_port):
    """
    Gère la communication entre 2 pairs. Ici, réception et affichage des données envoyées
    """
    try:
        global dht_local
        global responsability_plage
        data = msgpack.unpackb(conn.recv(1024))
        print(f"data:{data}")
        
        if data.get("action") == "Connection with the peer" :
            add_neighbor_peer(data, my_node, active_peers)
        if data.get("action") == "request_file" :
            handle_files(data, f'.storage{peer_port}')
            return dht_local
        if data.get("action") == "request_dht" or data.get("action") == "add_file" or data.get("action") == "send_dht" or data.get("action") == "delete_peer_dht":
            print(responsability_plage)
            dht_local = handle_dht(my_node,active_peers,data, dht_local, responsability_plage)
            responsability_plage = assign_dht(my_node, active_peers)
            return dht_local
        if data.get("action") == "looking_file" :
            time.sleep(1)
            request_list_peer_have_file(my_node,active_peers,data, dht_local, responsability_plage)
            return dht_local
        if data.get("action") == "lookin_file" :
            print("hello")
            localisation = data.get("data").get("localisation")
            key = data.get("data").get("key")
            print(localisation,key)
            request_files(localisation,key,my_node)
            return dht_local
        if data.get("action") == "replica_file" :
            applicant = data.get("data").get("applicant")
            key = data.get("data").get("key")
            count_peers_received = data.get("data").get("count_peers_received")
            print(applicant,key,count_peers_received)
            if count_peers_received < 3 and any(
                os.path.splitext(f)[0] == key for f in os.listdir(f".storage{peer_port}")):

                print(active_peers[count_peers_received%2],key)
                count_peers_received += 1
                print(count_peers_received%2)
                send_replica_message(my_node,[active_peers[count_peers_received%2]],key, count_peers_received )
                return dht_local
            else : 
                request_files([applicant],key,my_node, save_directory=f'.storage{peer_port}')
                message= {"action":"add_file", "data": {"key": key,"localisations": my_node}}
                dht_local=handle_dht(my_node,active_peers,message, dht_local, responsability_plage)
                return dht_local
        else :
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
                    s.sendall(msgpack.packb(message))
            except Exception as e:
                print(f"Peer connection error {peer_ip}:{peer_port} : {e}")


def add_neighbor_peer(data: str, my_node : list, active_peers:list,peer_port) -> None:
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
                    if peer[1:] !=['127.0.0.1',peer_port]:
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
 
# try:
#     while True:
#         print("\nActions disponibles :")
#         print("1. Tapez 'j' pour rejoindre le réseau.")
#         print("2. Tapez 'q' pour quitter le réseau.")
#         print("3. Tapez 'a' pour ajouter un fichier")
#         print("4. Tapez 'p' pour afficher les données du noeud")
#         print("5. Tapez 'r' pour demander un fichier")
#         action = input("Votre choix : ").lower()

#         if action == 'j':
#             port  = random.randint(1024, 65535)
#             my_node = [generate_key(f'127.0.0.1:{port}'),'127.0.0.1',port]
#             # active_peers = bootstrap_interaction("JOIN", active_peers,port)  # Tester l'action JOIN
#             result = bootstrap_interaction("JOIN", active_peers, port)
#             if result:
#                 active_peers = result[0]  # Récupère la liste des pairs actifs si elle est retournée

#                 # server_thread = threading.Thread(target=start_peer_server(port, my_node = my_node)) # Création d'un thread pour gérer la connexion entre 2 pairs avec la fonction start_peer_server
#                 server_thread = threading.Thread(target=start_peer_server, args=(port, my_node))

#                 server_thread.daemon = True
#                 server_thread.start()
#             # Se connecter aux autres pairs du réseau
#                 attempt_peer_connections(my_node)
#                 responsability_plage=assign_dht(my_node, active_peers)
#                 request_dht(my_node, active_peers, responsability_plage)
                
#                 file_path = "network_nodes.txt"
#                 with open(file_path, "a") as file:  
#                     file.write(f"Port: {port}, Node: {my_node}, Plage: {responsability_plage}\n")
            
#         elif action == 'q':
#             bootstrap_interaction("LEAVE", active_peers)  # Tester l'action LEAVE
#             break  # Sortie de la boucle après avoir quitté le réseau
#         # elif action == 'a' :
#         #     fichier = "IMG_20170915_173150.jpg"
#         #     fichier_coder,key = create_add_file_message(fichier, my_node)
#         #     add_file_to_network(fichier,f'.storage{PEER_PORT}')
#         #     time.sleep(1)
#         #     send_replica_message(my_node,active_peers,key)
#         #     data= {"action":"add_file", "data": fichier_coder}
#         #     dht_local=handle_dht(my_node,active_peers,data, dht_local, responsability_plage)
#         elif action == 'p':
#             print("Plage de responsabilité :", responsability_plage)
#             print("Liste des pairs actifs :", active_peers)
#             print("dht local :",dht_local)
#         elif action == 'r' :
#             message=create_looking_file_message("d82976927a30836e3d26fbdc83289539dc65229522676d071b3894e8478af059841e402823a16a394fe1c420483932a9b78ce18dcebe2a582c7fcb7f3faf33a2",my_node)
#             data= {"action":"looking_file", "data": message}
#             request_list_peer_have_file(my_node,active_peers,data, dht_local, responsability_plage)
#             #request_files([['127.0.0.1',7002],['127.0.0.1',7001]],"d82976927a30836e3d26fbdc83289539dc65229522676d071b3894e8478af059841e402823a16a394fe1c420483932a9b78ce18dcebe2a582c7fcb7f3faf33a2",my_node)

#         else:
#             print("Choix non valide. Veuillez taper une lettre valide")
            
# except KeyboardInterrupt:
#     print("\nInterruption par l'utilisateur. Déconnexion en cours...")
#     bootstrap_interaction("LEAVE", active_peers)
