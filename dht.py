import msgpack # type: ignore
import socket
import hashlib
import base64
from recup_ip import generate_key
from security import compute_pow, sign_message, verify_message_signature

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

# def create_message(fichier: str, peer: list) -> dict:
#     """
#     Crée un message contenant la clé générée pour un fichier et les localisations.
#     """
#     try:
#         with open(fichier, "rb") as f:
#             file_content = f.read()
#         key = generate_key(str(file_content))
#         message = {
#             "key": key,
#             "localisations": peer
#         }
#         return message
#     except FileNotFoundError:
#         print(f"Erreur : le fichier '{fichier}' est introuvable.")
#         return {}

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

def send_file(message:bytes, key:str, active_peers: list, start:int, end : int) -> None:
    """
    Envoie le fichier a son plus proche voisin
    """
    try :
        active_peers = sorted(active_peers, key=lambda peer: int(peer[0], 16))

        if end is None :
            target_peer = active_peers[0]
        else:
            if int(key, 16) < end or len(active_peers)<=1: 
                target_peer = active_peers[0]
            else:
                target_peer = active_peers[1]
        ip = target_peer[1]
        port = target_peer[2]
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((ip, port))
            client_socket.sendall(message)
    except Exception as e:
        print("Problème lors de l'envoi du fichier",e)

def request_dht(peer : list, active_peers: list, responsability_plage: tuple, private_key_pem: bytes) -> None:
    """
    Demande une plage spécifique de la DHT à un pair voisin.
    """
    try:
        start,end=responsability_plage
        request_message = {"action": "request_dht", "data": {"start": str(start), "end": str(end), "peer" : peer}}
         # Signature du message avant l'envoi
        #signed_message = create_signed_message(request_message, private_key_pem)

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

def send_dht_local(dht:dict,peer:list, start:int, end:int, private_key_pem: bytes) -> dict :
    """
    Envoie une plage de la dht local à un autre pair lors de la déconnexion
    avec peer qui est la liste du pair a qui envoyer la dht
    """
    try:
        filtered_dht = {}
        for key, value in dht.items() :
            key_int = int(str(key), 16)
            if end is not None :
                if start <= key_int <= end:
                    filtered_dht[key] = value
            else :
                if start<=key_int :
                    filtered_dht[key] = value
        message= {"action":"send_dht", "data": {"dht":filtered_dht}}
        #signed_message = create_signed_message(message, private_key_pem)
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


def handle_dht(peer: list, active_peers: list, received_data: dict, dht_local: dict, responsability_plage: tuple, private_key_pem: bytes) -> dict:
    """
    Gère les messages reçus qui ont pour but de modifier la DHT, en ajoutant une vérification de la signature
    """
    try:
        # Vérification de la signature du message
        signature = received_data.get("data", {}).get("signature")
        if   isinstance(signature, str) : 
            signature = base64.b64decode(signature)  # Convertir la signature en bytes
            data_without_signature = received_data["data"].copy()
            del data_without_signature["signature"]  # Retirer la signature avant vérification

            # 🔹 Ajout des prints pour débogage
            print(f"\n🔹 Données reçues pour vérification : {data_without_signature}")
            print(f"🔹 Signature reçue (base64) : {received_data['data']['signature']}")  # Afficher en base64
            #print(f"🔹 Signature reçue (bytes) : {signature}")

            signing_peer_public_key_pem = data_without_signature.get("public_key")  # Récupère la clé publique de l'envoyeur
            if not signing_peer_public_key_pem:
                print("❌ Clé publique de l'expéditeur non trouvée ! Message rejeté.")
                return dht_local

            if not verify_message_signature(data_without_signature, signature, signing_peer_public_key_pem.encode()):

            #if not verify_message_signature(data_without_signature, signature, public_key_pem):
                print("❌ La signature du message est invalide. Message rejeté.")
                return dht_local
            else:
                print("✅ La signature du message est valide.")
        #else:
            #print("Aucune signature reçue dans le message.")


        action = received_data.get("action")
        data = received_data.get("data")
        

        if action == "request_dht":
            start_recu = int(data.get("start"))
            end_recu = data.get("end")
            if end_recu in (None, "None"): 
                end_recu = None 
            else:
                end_recu = int(end_recu)
            start_peer, end_peer = responsability_plage

            if end_recu is None or end_peer is None: 
                if end_peer is None and start_recu >= start_peer: 
                    peer = data.get("peer")
                    return send_dht_local(dht_local, peer, start_recu, end_recu, private_key_pem)
                else: 
                    return dht_local
            else: 
                if (start_recu >= start_peer and end_recu <= end_peer): 
                    peer = data.get("peer")
                    return send_dht_local(dht_local, peer, start_recu, end_recu, private_key_pem)
                else:
                    return dht_local

        if action == "add_file":
            key = data.get("key")
            nonce = data.get("nonce")  # Récupération du nonce
            difficulty = 4  # Doit être le même que celui utilisé dans compute_pow()
            
            # # 🔹 Demander aux pairs de vérifier le PoW
                
            # is_valid = request_pow_verification(active_peers, key, nonce, difficulty)

            # if not is_valid:
            #     print(f"❌ PoW invalide ! Rejet du fichier avec clé {key}")
            #     return dht_local

            # print(f"✅ PoW validé par les pairs ! Le fichier avec clé {key} est accepté.")
        
        
            

            # Vérification du PoW
            hash_value = hashlib.sha256(f"{key}{nonce}".encode()).hexdigest()
            if nonce is None or hash_value[:difficulty] != "0" * difficulty:
                print(f"❌ PoW invalide ! Rejet du fichier avec clé {key}")
                return dht_local

            print(f"✅ PoW valide ! Le fichier avec clé {key} est accepté.")
            
            key_int = int(key, 16)
            print(key_int)
            start, end = assign_dht(peer, active_peers)
            if end is not None:
                if (key_int >= start and key_int < end) or (end is None and key_int >= start):
                    localisations = data.get("localisations")
                    return add_file_to_dht_local(dht_local, key, [localisations])
                else:
                    message = msgpack.packb(received_data)
                    send_file(message, key, active_peers, start, end)
                    return dht_local

            if (end is None and key_int >= start): 
                localisations = data.get("localisations")
                return add_file_to_dht_local(dht_local, key, [localisations])
            else:
                message = msgpack.packb(received_data)
                send_file(message, key, active_peers, start, end)
                return dht_local

        if action == "send_dht":
            dht_recu = data.get("dht", {})
            return merge_dht(dht_local, dht_recu)
        else: 
            return dht_local

    except Exception as e:
        print(f"Problème avec la handle_dht : {e}")
        return dht_local


def create_message(fichier: str, peer: list, private_key_pem: bytes, public_key_pem: bytes) : #public_key_pem: bytes) -> dict:
    """
    Crée un message contenant la clé générée pour un fichier, les localisations, la preuve de travail,
    et la signature du message pour assurer son authenticité.
    """
    try:
        with open(fichier, "rb") as f:
            file_content = f.read()
        
        # Génération de la clé et du nonce pour la preuve de travail
        key = generate_key(str(file_content))
        nonce = compute_pow(key, difficulty=4)  # Génère un nonce valide
        
        # Création du message
        message = {
            "key": key,
            "localisations": peer,
            "nonce": nonce,  # Ajoute le nonce pour prouver le PoW
            #"public_key": base64.b64encode(public_key_pem).decode()  # 🔹 Encodage en base64 pour éviter les problèmes

            "public_key": public_key_pem.decode()  # Ajoute la clé publique dans le message
        }
        
        # Signature du message
        signature = sign_message(message, private_key_pem)
        message["signature"] = base64.b64encode(signature).decode("utf-8")  # Convertit en string compatible JSON
        


        # 🔹 Ajout des prints pour débogage
        print(f"\n🔹 Message signé : {message}")
        #print(f"🔹 Signature (base64) : {message['signature']}")
              
        return message

    except FileNotFoundError:
        print(f"Erreur : le fichier '{fichier}' est introuvable.")
        return {}


def create_signed_message(message: dict, private_key_pem: bytes) -> dict:
    """
    Signe un message générique avec la clé privée.
    """
    try:
        # Signature du message
        signature = sign_message(message, private_key_pem)
        message["signature"] = base64.b64encode(signature).decode("utf-8")  # Convertit en string compatible JSON
        
        # 🔹 Debugging
        print(f"\n🔹 Message signé : {message}")
        print(f"🔹 Signature (base64) : {message['signature']}")
        
        return message

    except Exception as e:
        print(f"Erreur lors de la signature du message : {e}")
        return {}
