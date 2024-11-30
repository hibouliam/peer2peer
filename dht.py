import msgpack # type: ignore
import socket
from recup_ip import generate_key

active_peers =[['8d63f136a918f183a00e2d6059d09e1493a4286a9c34a41d05c522afde3ab5834fc99aa62bf6fe7867739749015c63b5135f2c7091bb4078d1cc27d8cdaecb87', '127.0.0.1', 7003]]
peer = ['b048dee8bf0ca95792006780bf7cff3a68cb4e37ff35b36313bd83576b02021ce7c0410b8a35613f6ae26507e788f7d4d6af389ec716a9c95729b486e063b20e', '127.0.0.1', 7004]

def assign_dht(my_node: list,active_peers:list) -> tuple :
    """
    Asssigne la plage de la dht au pair en fonction de ses voisins en utilisant la fonction determine_responsibility
    """
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
    



dht = {}  

def create_message(fichier: str, peer: list) -> dict:
    """
    Crée un message contenant la clé générée pour un fichier et les localisations.
    """
    try:
        with open(fichier, "rb") as f:
            file_content = f.read()
        key = generate_key(str(file_content))
        message = {
            "key": key,
            "localisations": peer
        }
        print(message)
        return message
    except FileNotFoundError:
        print(f"Erreur : le fichier '{fichier}' est introuvable.")
        return {}

def add_file_to_dht_local(dht:dict, key:str, localisations:list)->  dict :
    """
    Ajoute un fichier à la DHT local.
    """
    if key in dht :
        for peer in localisations :
            if peer not in dht[key] :
                dht[key].append(peer)
        return dht
    else :
        dht[key]=localisations
        return dht

def send_file(message:bytes, key:str, active_peers: list, start:int, end : int) -> None:
    """
    Envoie le fichier a son plus proche voisin
    """
    try :
        active_peers = sorted(active_peers, key=lambda peer: int(peer[0], 16))

        if int(key, 16) < end or len(active_peers)<=1: 
            target_peer = active_peers[0]
        else:
            target_peer = active_peers[1]
        ip = target_peer[1]
        port = target_peer[2]
        print(f"tar{target_peer}")
        print(msgpack.unpackb(message),ip,port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((ip, port))
            client_socket.sendall(message)
    except Exception as e:
        print("Problème lors de l'envoi du fichier",e)

def request_dht(peer : list, active_peers: list, responsability_plage: tuple) -> None:
    """
    Demande une plage spécifique de la DHT à un pair voisin.
    """
    try:
        start,end=responsability_plage
        request_message = {"action": "request_dht", "data": {"start": str(start), "end": str(end), "peer" : peer}}
        packed_request = msgpack.packb(request_message)
        print(responsability_plage)
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
        for key, value in dht.items() :
            print(key,value)
            key_int = int(str(key), 16)
            if end is not None :
                if start <= key_int <= end:
                    filtered_dht[key] = value
                    print(filtered_dht)
            else :
                if start<=key_int :
                    filtered_dht[key] = value
                    print(filtered_dht)
        message= {"action":"send_dht", "data": {"dht":filtered_dht}}
        msgpack_dht = msgpack.packb(message)
        ip = peer[1]
        port = peer[2]
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

def handle_dht(peer:list, active_peers: list, received_data:dict,dht_local:dict, responsability_plage: tuple) -> dict :
    """
    Gère les messages recu qui ont pour but de modifier a dht
    """
    try :
        print("coucou")
        action = received_data.get("action")
        data = received_data.get("data")
        if action == "request_dht" :
            print("coucou")
            start_recu = int(data.get("start"))
            end_recu = data.get("end")
            if end_recu in (None, "None"): 
                end_recu = None 
            else:
                end_recu = int(end_recu)
            start_peer,end_peer= responsability_plage
            
            print(start_recu, end_recu, start_peer, end_peer)
            if end_recu is None or end_peer is None : 
                if end_peer is None and start_recu >= start_peer : 
                    
                    peer = data.get("peer")
                    print(peer)
                    return send_dht_local(dht_local, peer, start_recu, end_recu)
                else : 
                    return dht_local
            else : 
                if (start_recu>=start_peer and end_recu<=end_peer) : 
                    
                    peer = data.get("peer")
                    print(peer)
                    print(type(peer))
                    print(peer[1])
                    return send_dht_local(dht_local, peer, start_recu, end_recu)
            # if (start_recu>=start_peer and end_recu<=end_peer) or (end_recu is None and end_peer is None and start_recu>start_peer):
            #     peer = data.get("peer")
            #     return send_dht_local(dht_local, peer, start_recu, end_recu)
                else:
                    return dht_local
                
        if action == "add_file":
            key=data.get("key")
            key_int=int(key,16)
            start,end=assign_dht(peer, active_peers)
            if end is not None :
                if (key_int>=start and key_int<end) or (end is None and key_int>=start):
                    localisations = data.get("localisations")
                    return add_file_to_dht_local(dht_local, key, localisations)
                else :
                    message = msgpack.packb(received_data)
                    send_file(message, key,active_peers, start, end)
                    return dht_local
                
            if (end is None and key_int>=start): 
                localisations = data.get("localisations")
                return add_file_to_dht_local(dht_local, key, localisations)
            else :
                message = msgpack.packb(received_data)
                send_file(message, key,active_peers, start, end)
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