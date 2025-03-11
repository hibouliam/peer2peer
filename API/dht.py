import msgpack # type: ignore
import socket
from recup_ip import generate_key
import time

def assign_dht(my_node: list,active_peers:list) -> tuple :
    """
    Asssigne la plage de la dht au pair en fonction de ses voisins en utilisant la fonction determine_responsibility
    """
    if active_peers == None :
        return (0,None)
    if len(active_peers) == 0 :
        return (0,None)
    
    my_node_key = int(my_node [0],16)
    left_neighbor_key = int(active_peers [0][0],16)

    if len(active_peers) == 1 :
        if(my_node_key < left_neighbor_key):
            return (0,left_neighbor_key)
        else :
            return (my_node_key,None)


    right_neighbor_key = int(active_peers [1][0],16)
    return determine_responsibility (my_node_key,left_neighbor_key,right_neighbor_key)



def determine_responsibility(peer_key : int, left_neighbor_key : int, right_neighbor_key :int) -> tuple:
    """
    Détermine la plage de responsabilité pour un pair dans une DHT allant de 0 à +infini.
    - si ses deux voisins sont plus grands alors il est reponsable de 0 au voisin le plus proche de lui (par exemple si 1 a comme voisin 2 et 5 alors il responsable de 0 à 2 )
    - si ses deux voisins sont plus petits alors il est reponsable  de lui à +infini (par exemple si 5 a comme voisin 1 et 4 alors il est responable de 5 à +infini)
    - sinon il est responsable de lui à son voisin le plus grand
    """

    if left_neighbor_key> peer_key and right_neighbor_key> peer_key :
        return (0, min(left_neighbor_key,right_neighbor_key))
    if left_neighbor_key< peer_key and right_neighbor_key<peer_key :
        return (peer_key, None)
    else :
        return(peer_key, max(left_neighbor_key,right_neighbor_key))
    



############### Demande de localisation des fichiers ##########################

def create_looking_file_message(looking_key: str, my_node : list ) -> dict :
    """
    Crée un message pour chercher un fichier à la dht
    """
    try :
        message = {
            "action":"looking_file", #Sert surement a rien a vérifier
            "key": looking_key,
            "applicant": my_node
        }
        return message
    except Exception as e:
        print("Problème lors de create_looking_file_message",e)
        return {}

def send_localisations(applicant_peer:list, looking_key:str, dht_local:dict) -> None :
    """
    Envoie la liste des paires qui ont le fichier recherché ou envoie le fichier n'existe si la key n'existe pas
    """
    if looking_key in dht_local:
        message={"key": looking_key,
                "localisation": dht_local[looking_key]
                }
    else:
        message={"key": looking_key,
                "localisation": "n'existe pas"
                }
    data= {"action":"lookin_file", "data": message}
    data_packb = msgpack.packb(data)
    ip = applicant_peer[1]
    port = applicant_peer[2]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((ip, port))
        client_socket.sendall(data_packb)  
        
def request_list_peer_have_file(peer:list, active_peers: list, received_data:dict,dht_local:dict, responsability_plage: tuple ) -> None :
    data= received_data.get("data")
    key = data.get("key")
    key_int=int(key,16)
    print(key_int)
    start,end=assign_dht(peer, active_peers)
    print(start,end)
    if end is not None :
        if (key_int>=start and key_int<end) or (end is None and key_int>=start):
            return send_localisations(data.get("applicant"),key,dht_local)
        else :
            message = msgpack.packb(received_data)
            send_message_close_peer(message, key,active_peers, start, end)
            return dht_local
                
    if (end is None and key_int>=start): 
        return send_localisations(data.get("applicant"),key,dht_local)
    else :
        message = msgpack.packb(received_data)
        send_message_close_peer(message, key,active_peers, start, end)
        return dht_local
    
############### Gestion de réplica des fichiers ##########################

def create_replica_message(replica_key: str, my_node : list, count_peers_received ) -> dict :
    """
    Crée un message pour chercher un fichier à la dht
    """
    try :
        message = {
            "action":"replica_file", #Sert surement a rien a vérifier
            "key": replica_key,
            "applicant": my_node,
            "count_peers_received" :  count_peers_received
        }
        return message
    except Exception as e:
        print("Problème lors de create_replica_message",e)
        return {}

def send_replica_message(my_node:list, active_peers: list, replica_key :str, count_peers_received = 0 ) -> None :
    message = create_replica_message(replica_key, my_node, count_peers_received)
    data= {"action":"replica_file", "data": message}
    msgpack_dht = msgpack.packb(data)
    for peer in active_peers :
        ip = peer[1]
        port = peer[2]
        print(ip,port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((ip, port))
            client_socket.sendall(msgpack_dht)
    


############### Ajout des fichiers dans la DHT ##########################

def create_add_file_message(fichier: str, peer: list) -> dict:
    """
    Crée un message pour ajouter un fichier à la dht
    contenant la clé générée pour un fichier et les localisations.
    """
    try:
        with open(fichier, "rb") as f:
            file_content = f.read()
        key = generate_key(str(file_content))
        message = {
            "key": key,
            "localisations": peer
        }
        return message,key
    except FileNotFoundError:
        print(f"Erreur : le fichier '{fichier}' est introuvable.")
        return {}

def add_file_to_dht_local(dht:dict, key:str, localisations:list)->  dict :
    """
    Ajoute un fichier à la DHT local.
    Type de la dht {'key':[peer1,peer2...]}
    """
    
    print(localisations)
    if key in dht:
        for peer in localisations:
            if peer not in dht[key]:  
                dht[key].append(peer)
    else:
        # Initialiser avec des listes pour chaque peer
        dht[key]=localisations
    
    return dht


############## Suppression d'un pair dans une DHT #######################

def create_delete_file_message(key: str, peer: list) -> dict:
    """
    Crée un message pour ajouter un fichier à la dht
    contenant la clé générée pour un fichier et les localisations.
    """
    try:
        message = {
            "key": key,
            "localisations": peer
        }

        return message
    except FileNotFoundError:
        print(f"Erreur :create_delete_file_message.")
        return {}
    
def remove_peer_from_dht(dht: dict, file_key: str, peer_to_remove: tuple):
    """
    Supprime un pair spécifique de la DHT pour une clé donnée.

    """
    if file_key in dht:
        print(peer_to_remove)
        dht[file_key] = [peer for peer in dht[file_key] if (print(f"Comparaison: {peer} avec {peer_to_remove}") or peer != peer_to_remove)]
        
        # Supprimer la clé si plus aucun pair n'a ce fichier
        if not dht[file_key]:
            del dht[file_key]

        print(f"Pair {peer_to_remove} supprimé de {file_key}")
        return dht
    else:
        print(f"Clé {file_key} introuvable dans la DHT.")
        return dht

############### Envoie de message entre paires ##########################

def send_message_close_peer(message:bytes, key:str, active_peers: list, start:int, end : int) -> None:
    """
    Envoie le fichier a son plus proche voisin
    """
    try :
        active_peers = sorted(active_peers, key=lambda peer: int(peer[0], 16))

        if end is None :
            print("coucou")
            target_peer = active_peers[1]
        else:
            if int(key, 16) < end or len(active_peers)<=1: 
                target_peer = active_peers[0]
            else:
                target_peer = active_peers[1]
        ip = target_peer[1]
        port = target_peer[2]
        print(ip,port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((ip, port))
            client_socket.sendall(message)
    except Exception as e:
        print("Problème lors de l'envoi du fichier",e)

############### Gestion de la dht en fonction des connnexions et déconnexions ##########################

def request_dht(peer : list, active_peers: list, responsability_plage: tuple) -> None:
    """
    Demande une plage spécifique de la DHT à un pair voisin.
    """
    try:
        start,end=responsability_plage
        request_message = {"action": "request_dht", "data": {"start": str(start), "end": str(end), "peer" : peer}}
        packed_request = msgpack.packb(request_message)
        for peer in active_peers :
            ip = peer[1]
            port = peer[2]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((ip, port))
                client_socket.sendall(packed_request)

    except Exception as e:
        print(f"Erreur lors de la demande de DHT à : {e}")
        return {}

def send_dht_local(dht:dict,peer:list, start:int, end:int) -> dict :
    """
    Envoie une plage de la dht local à un autre pair lors de la déconnexion
    avec peer qui est la liste du pair a qui envoyer la dht
    """
    try:
        filtered_dht = {}
        print(dht)
        for key, value in dht.items() :
            key_int = int(str(key), 16)
            if end is not None :
                if start <= key_int <= end:
                    filtered_dht[key] = value
            else :
                if start<=key_int :
                    filtered_dht[key] = value
        print(filtered_dht)
        message= {"action":"send_dht", "data": {"dht":filtered_dht}}
        msgpack_dht = msgpack.packb(message)
        ip = peer[1]
        port = peer[2]
        print(ip,port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((ip, port))
            client_socket.sendall(msgpack_dht)

        for key in list(filtered_dht.keys()):
            del dht[key]
        return dht
    except Exception as e:
        print(f"Erreur lors de l'envoi de la DHT à {peer}: {e}")

def merge_dht(dht_local:dict, dht_recu:dict) -> dict :
    """
    Fusionne la dht du peer qui se déconnecte avec la sienne
    """
    for key, localisations in dht_recu.items():
        dht_local=add_file_to_dht_local(dht_local,key,localisations)
    return dht_local

############### Gestion des messages recu ##########################

def handle_dht(peer:list, active_peers: list, received_data:dict,dht_local:dict, responsability_plage: tuple) -> dict :
    """
    Gère les messages recu qui ont pour but de modifier a dht 
    """
    try :
        action = received_data.get("action")
        data = received_data.get("data")
        print(action,data)
        if action == "request_dht" :
            print("j")
            start_recu = int(data.get("start"))
            end_recu = data.get("end")
            peer = data.get("peer")
            
            if end_recu in (None, "None"): 
                end_recu = None 
            else:
                end_recu = int(end_recu)
            start_peer,end_peer= responsability_plage
            print(start_peer,end_peer)
            # Cas où end_peer est None (je suis responsable de toute la plage restante)
            if end_peer is None:
                if start_recu >= start_peer:
                    print(f"Sending DHT to {peer}")
                    return send_dht_local(dht_local, peer, start_recu, end_recu)
                else:
                    print("Request does not match my responsibility range.")
                    return dht_local

            # Cas où end_recu est None (le demandeur ne connaît pas sa fin)
            if end_recu is None:
                if start_recu >= start_peer:
                    print(f"Sending partial DHT to {peer}")
                    return send_dht_local(dht_local, peer, start_recu, end_recu)
                else:
                    print("Request does not match my responsibility range.")
                    return dht_local

            # Cas général : Vérifier si les plages se chevauchent
            if (start_recu >= start_peer and (end_recu is None or end_recu <= end_peer)):
                print(f"Sending matched DHT to {peer}")
                return send_dht_local(dht_local, peer, start_recu, end_recu)
            
            print("No matching DHT range found.")
            return dht_local
                
        if action == "add_file" or action == "delete_peer_dht":
            time.sleep(5)
            print("hel")
            print(data)
            key=data.get("key")
            key_int=int(key,16)
            print(key)
            print(key_int)
            start,end=assign_dht(peer, active_peers)
            print(start,end)
            if end is not None :
                if (key_int>=start and key_int<end) or (end is None and key_int>=start):
                    if action  == "add_file" :
                        localisations = data.get("localisations")
                        return add_file_to_dht_local(dht_local, key, [localisations])
                    if action  == "delete_peer_dht" :
                        peer_to_remove = data.get("localisations")
                        dht_local = remove_peer_from_dht (dht_local, key, peer_to_remove)
                        print(dht_local)
                        return dht_local
                else :
                    message = msgpack.packb(received_data)
                    send_message_close_peer(message, key,active_peers, start, end)
                    return dht_local
                
            if (end is None and key_int>=start): 
                if action  == "add_file" :
                    localisations = data.get("localisations")
                    return add_file_to_dht_local(dht_local, key, [localisations])
                if action  == "delete_peer_dht" :
                    peer_to_remove = data.get("localisations")
                    dht_local = remove_peer_from_dht (dht_local, key, peer_to_remove)
                    print(dht_local)
                    return dht_local
            else :
                message = msgpack.packb(received_data)
                send_message_close_peer(message, key,active_peers, start, end)
                return dht_local
            
        if action == "send_dht":
            dht_recu=data.get("dht", {})
            return merge_dht(dht_local, dht_recu)
        else : 
            return dht_local
    except Exception as e:
        print(f"problème avec la handle_dht : {e}")

'''
Lorsqu'un pair se connecte il demande la dht en fonction de ce qui est assigné
Donc étape 1 connexion :avoir sa liste active peer 
                        puis faire la fonction assign_dht pour avoir start et end
                        Demander la dht a ses pairs avec un start et end grâce a requiert_dht(en fonction de son assign_dht)                        
                        Intégration de la dht recu grace dans la dht_local grace à handle_dht
            
        pair demande dht : Réajuste son start et end grâce à assign_dht
                           Envoie + supprime de de la dht en fonction du start et end avec la fonction send_dht 
                           
                         

            déconnexion : Envoie toute sa dht au pair concerné 


'''