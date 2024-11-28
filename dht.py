import msgpack # type: ignore
import socket
import json
import unittest
from unittest.mock import patch, MagicMock

active_peers =[['5fe96ad748b11f2e00af23d0899e1bcff4655811831499732e5193937e3c8072fc9f44060acb7db8a3969c0a3df7fc5f52f0607d137bd684725081e6c3894f19', '127.0.0.1', 7001], ['b048dee8bf0ca95792006780bf7cff3a68cb4e37ff35b36313bd83576b02021ce7c0410b8a35613f6ae26507e788f7d4d6af389ec716a9c95729b486e063b20e', '127.0.0.1', 7004]]
peer = ['6fe96ad748b11f2e00af23d0899e1bcff4655811831499732e5193937e3c8072fc9f44060acb7db8a3969c0a3df7fc5f52f0607d137bd684725081e6c3894f19', '127.0.0.1', 7002]

def assign_dht(peer: list,active_peers:list) -> tuple :
    """
    Asssigne la plage de la dht au pair en fonction de ses voisins en utilisant la fonction determine_responsibility
    """
    peer_key = int(peer [0],16)
    
    left_neighbor_key = int(active_peers [0][0],16)
    right_neighbor_key = int(active_peers [1][0],16)
    return determine_responsibility (peer_key,left_neighbor_key,right_neighbor_key)


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
        if int(key, 16) > end:
            target_peer = active_peers[2]
        else:
            target_peer = active_peers[1]

        ip = target_peer[1]
        port = target_peer[2]
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((ip, port))
            client_socket.sendall(message)
    except :
        print("Problème lors de l'envoi du fichier")


def request_dht(active_peers: list, start: int, end: int) -> None:
    """
    Demande une plage spécifique de la DHT à un pair voisin.
    """
    request_message = {"action": "request_dht", "data": {"start": start, "end": end}}
    packed_request = msgpack.packb(request_message)
    for peer in active_peers:
        try:
            ip = peer[1]
            port = peer[2]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((ip, port))
                client_socket.sendall(packed_request)
        except Exception as e:
            print(f"Erreur lors de la demande de DHT à {peer}: {e}")



def send_dht_local(dht:dict,peer:list, start:int, end:int) -> None :
    """
    Envoie une plage de la dht local à un autre pair lors de la déconnexion
    avec peer qui est la liste du pair a qui envoyer la dht
    """
    try:
        filtered_dht = {key: value for key, value in dht.items() if start <= int(key,16) <= end}
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


def handle_dht(peer: list, active_peers: list, message: bytes, dht_local: dict) -> dict:
    """
    Gère les messages reçus qui ont pour but de modifier la DHT.
    """
    try:
        # Vérifier si le message est textuel
        if message.startswith(b"Successful connection with the peer"):
            # Convertir le message en chaîne de caractères
            text_message = message.decode('utf-8')
            print(f"Message textuel reçu : {text_message}")

            # Extraire les informations JSON après le préfixe
            prefix = "Successful connection with the peer "
            json_data = text_message[len(prefix):].strip()
            json_data = json_data.replace("'", '"')  # Remplacer les simples quotes par des doubles quotes
            data = json.loads(json_data)

            print(f"Données extraites : {data}")
            # Traitez les données extraites ici si nécessaire
            return

        # Si le message est en MsgPack
        print(f"Message brut reçu : {message}")
        received_data = msgpack.unpackb(message, strict_map_key=False)
        print(f"Données reçues après unpack : {received_data}")

        action = received_data.get("action")
        data = received_data.get("data")
        print(f"Action : {action}, Données : {data}")

        if action == "request_dht":
            start_recu = int(data.get("start"))
            end_recu = int(data.get("end"))
            start_peer, end_peer = assign_dht(peer, active_peers)
            if (start_recu >= start_peer and end_recu <= end_peer) or (
                end_recu is None and end_peer is None and start_recu > start_peer
            ):
                return send_dht_local(dht_local, peer, start_recu, end_recu)
            else:
                return

        elif action == "add_file":
            key = int(data.get("key"), 16)
            start, end = assign_dht(peer, active_peers)
            if (key > start and key < end) or (end is None and key > start):
                localisations = data.get("localisations")
                return add_file_to_dht_local(dht_local, key, localisations)
            else:
                return send_file(message, key, active_peers, start, end)

        elif action == "send_dht":
            dht_recu = data.get("dht", {})
            return merge_dht(dht_local, dht_recu)

        else:
            print(f"Action non reconnue : {action}")

    except json.JSONDecodeError as e:
        print(f"Erreur lors du décodage JSON : {e}")
    except msgpack.ExtraData as e:
        print(f"Problème avec handle_dht : données supplémentaires détectées ({e}).")
        print(f"Données restantes : {e.extra}")
    except Exception as e:
        print(f"Problème avec handle_dht : {e}")

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