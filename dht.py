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
        #return dht
    except Exception as e:
        print(f"Erreur lors de l'envoi de la DHT à {peer}: {e}")

    # Toujours retourner la DHT mise à jour
    return dht


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
Donc étape 1 connexion : avoir sa liste active peer 
                        puis faire la fonction assign_dht pour avoir start et end
                        Demander la dht a ses pairs avec un start et end grâce a requiert_dht(en fonction de son assign_dht)                        
                        Intégration de la dht recu grace dans la dht_local grace à handle_dht
            
        pair demande dht : Réajuste son start et end grâce à assign_dht
                           Envoie + supprime de de la dht en fonction du start et end avec la fonction send_dht 
                           
                         

            déconnexion : Envoie toute sa dht au pair concerné 


'''

################## TEST ####################

## TEST fonction determine_responsability#
def test_determine_responsibility_example():
    # Exemple concret
    peer_id = 15
    predecessor_id = 10
    successor_id = 20
    
    # Appeler la fonction
    result = determine_responsibility(peer_id, predecessor_id, successor_id)
    
    # Afficher le résultat
    print(f"Responsabilité déterminée pour peer_id={peer_id}, "
          f"predecessor_id={predecessor_id}, successor_id={successor_id} : {result}")
    
    # Vérifier manuellement (ou en mode script)
    assert result == (15, 20), "Test échoué : le résultat attendu est (15, 20)"

# Appel du test
#test_determine_responsibility_example()



# TEST Function add_file_to_dht_local
def test_add_file_to_dht_local():
    # Initialisation
    dht = {}

    # Test 1 : Ajouter un fichier qui n'existe pas encore
    print("\nTest 1: Ajouter un fichier nouveau")
    key = "file1"
    localisations = ["peer1", "peer2"]
    dht = add_file_to_dht_local(dht, key, localisations)
    print(f"DHT après ajout : {dht}")
    assert dht == {"file1": ["peer1", "peer2"]}, "Test 1 échoué : le fichier n'a pas été correctement ajouté."

    # Test 2 : Ajouter une nouvelle localisation pour un fichier existant
    print("\nTest 2: Ajouter une localisation pour un fichier existant")
    key = "file1"
    localisations = ["peer2", "peer3"]
    dht = add_file_to_dht_local(dht, key, localisations)
    print(f"DHT après ajout : {dht}")
    assert dht == {"file1": ["peer1", "peer2", "peer3"]}, "Test 2 échoué : la localisation n'a pas été correctement ajoutée."

    # Test 3 : Ajouter un autre fichier
    print("\nTest 3: Ajouter un autre fichier")
    key = "file2"
    localisations = ["peer4"]
    dht = add_file_to_dht_local(dht, key, localisations)
    print(f"DHT après ajout : {dht}")
    assert dht == {"file1": ["peer1", "peer2", "peer3"], "file2": ["peer4"]}, "Test 3 échoué : le second fichier n'a pas été correctement ajouté."

    print("\nTous les tests ont réussi ! 🎉")

# Exécution du test
#test_add_file_to_dht_local()

# TEST function send_file
class TestSendFile(unittest.TestCase):
    @patch("socket.socket")  # Mock du socket
    def test_send_file(self, mock_socket):
        # Mock du socket client
        mock_client_socket = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_client_socket

        # Paramètres de test
        message = b"Test message"
        key = "7fabc123"  # En hexadécimal
        active_peers = [
            ["5fabc123", "127.0.0.1", 7001],
            ["6fabc123", "127.0.0.2", 7002],
            ["8fabc123", "127.0.0.3", 7003]
        ]
        start = int("5fabc123", 16)
        end = int("6fabc123", 16)

        # Appel de la fonction
        send_file(message, key, active_peers, start, end)

        # Vérification que le socket a été créé
        mock_socket.assert_called_once()

        # Vérification que la connexion a été faite avec le bon pair (127.0.0.3, 7003)
        mock_client_socket.connect.assert_called_with(("127.0.0.3", 7003))

        # Vérification que le message a été envoyé au pair sélectionné
        mock_client_socket.sendall.assert_called_once_with(message)


class TestRequestDHT(unittest.TestCase):
    
    @patch("socket.socket")  # Mock de la fonction socket
    def test_request_dht(self, mock_socket):
        # Mock du client socket
        mock_client_socket = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_client_socket

        # Paramètres de test
        active_peers = [
            ["peer1", "127.0.0.1", 7001],
            ["peer2", "127.0.0.2", 7002]
        ]
        start = 10
        end = 20

        # Appel de la fonction
        request_dht(active_peers, start, end)

        # Création du message attendu
        expected_message = {"action": "request_dht", "data": {"start": start, "end": end}}
        packed_request = msgpack.packb(expected_message)

        # Vérification des appels
        self.assertEqual(mock_client_socket.connect.call_count, len(active_peers))
        self.assertEqual(mock_client_socket.sendall.call_count, len(active_peers))
        mock_client_socket.sendall.assert_called_with(packed_request)

    @patch("socket.socket")
    def test_request_dht_error(self, mock_socket):
        # Mock du socket avec erreur de connexion
        mock_client_socket = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_client_socket
        mock_client_socket.connect.side_effect = socket.error("Connection failed")

        # Paramètres de test
        active_peers = [
            ["peer1", "127.0.0.1", 7001],
            ["peer2", "127.0.0.2", 7002]
        ]
        start = 10
        end = 20

        # Appel de la fonction (ne doit pas lever d'exception)
        request_dht(active_peers, start, end)

        # Vérification que la connexion a échoué pour chaque pair
        self.assertEqual(mock_client_socket.connect.call_count, len(active_peers))
        mock_client_socket.sendall.assert_not_called()  # Ne doit pas envoyer de message

    @patch("socket.socket")
    def test_request_dht_no_peers(self, mock_socket):
        # Liste vide de pairs
        active_peers = []
        start = 10
        end = 20

        # Appel de la fonction
        request_dht(active_peers, start, end)

        # Aucun appel à connect ou sendall ne doit avoir lieu
        mock_socket.return_value.__enter__.return_value.connect.assert_not_called()
        mock_socket.return_value.__enter__.return_value.sendall.assert_not_called()

if __name__ == "__main__":
    unittest.main()

"""    

class TestSendDHTLocal(unittest.TestCase):
    @patch("socket.socket")
    def test_send_dht_local_success(self, mock_socket):
        # Mock du socket
        mock_client_socket = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_client_socket

        # Données de test
        dht = {
            "1a": "value1",
            "2b": "value2",
            "3c": "value3",
            "4d": "value4"
        }
        peer = ["peer1", "127.0.0.1", 7001]
        start = int("2b", 16)
        end = int("3c", 16)

        # Appel de la fonction
        updated_dht = send_dht_local(dht, peer, start, end)

        # DHT filtrée attendue
        filtered_dht = {
            "2b": "value2",
            "3c": "value3"
        }

        # Message attendu
        expected_message = {"action": "send_dht", "data": {"dht": filtered_dht}}
        packed_message = msgpack.packb(expected_message)

        # Vérifications
        mock_client_socket.connect.assert_called_once_with((peer[1], peer[2]))
        mock_client_socket.sendall.assert_called_once_with(packed_message)

        # Vérification que les clés filtrées ont été supprimées
        expected_updated_dht = {
            "1a": "value1",
            "4d": "value4"
        }
        self.assertEqual(updated_dht, expected_updated_dht)

    @patch("socket.socket")
    def test_send_dht_local_error(self, mock_socket):
        # Mock du socket avec une erreur de connexion
        mock_client_socket = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_client_socket
        mock_client_socket.connect.side_effect = socket.error("Connection failed")

        # Données de test
        dht = {
            "1a": "value1",
            "2b": "value2",
            "3c": "value3",
            "4d": "value4"
        }
        peer = ["peer1", "127.0.0.1", 7001]
        start = int("2b", 16)
        end = int("3c", 16)

        # Appel de la fonction (ne doit pas lever d'exception)
        updated_dht = send_dht_local(dht, peer, start, end)

        # Vérification que la DHT d'origine reste inchangée
        self.assertEqual(updated_dht, dht)

    def test_send_dht_local_no_matching_keys(self):
        # Cas où aucune clé ne correspond à la plage
        dht = {
            "1a": "value1",
            "4d": "value4"
        }
        peer = ["peer1", "127.0.0.1", 7001]
        start = int("2b", 16)
        end = int("3c", 16)

        # Appel de la fonction
        updated_dht = send_dht_local(dht, peer, start, end)

        # Vérification que la DHT reste inchangée
        self.assertEqual(updated_dht, dht)

    @patch("socket.socket")
    def test_send_dht_local_invalid_peer(self, mock_socket):
        # Cas où le pair est invalide
        mock_client_socket = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_client_socket

        # Données de test
        dht = {
            "1a": "value1",
            "2b": "value2"
        }
        peer = ["peer1", None, None]  # IP et port invalides
        start = int("1a", 16)
        end = int("2b", 16)

        # Appel de la fonction (ne doit pas lever d'exception)
        updated_dht = send_dht_local(dht, peer, start, end)

        # Vérification que la DHT reste inchangée
        self.assertEqual(updated_dht, dht)


import unittest

class TestMergeDHT(unittest.TestCase):
    def setUp(self):
        # Fonction mockée pour simuler l'ajout de fichiers à la DHT locale
        def mock_add_file_to_dht_local(dht_local, key, localisations):
            if key not in dht_local:
                dht_local[key] = localisations
            else:
                # Ajouter les localisations reçues qui ne sont pas déjà présentes
                for loc in localisations:
                    if loc not in dht_local[key]:
                        dht_local[key].append(loc)
            return dht_local

        # Remplacer la fonction dans le scope du test
        global add_file_to_dht_local
        add_file_to_dht_local = mock_add_file_to_dht_local

    def test_merge_dht_success(self):
        # Données de test
        dht_local = {
            "file1": ["peer1"],
            "file2": ["peer2"]
        }
        dht_recu = {
            "file2": ["peer3"],  # Mise à jour d'un fichier existant
            "file3": ["peer4"]   # Nouveau fichier
        }

        # Appel de la fonction
        merged_dht = merge_dht(dht_local, dht_recu)

        # DHT attendue après la fusion
        expected_dht = {
            "file1": ["peer1"],
            "file2": ["peer2", "peer3"],
            "file3": ["peer4"]
        }

        # Vérification
        self.assertEqual(merged_dht, expected_dht)

    def test_merge_dht_empty_recu(self):
        # Données de test
        dht_local = {
            "file1": ["peer1"]
        }
        dht_recu = {}  # DHT reçue vide

        # Appel de la fonction
        merged_dht = merge_dht(dht_local, dht_recu)

        # La DHT locale ne change pas
        self.assertEqual(merged_dht, dht_local)

    def test_merge_dht_empty_local(self):
        # Données de test
        dht_local = {}  # DHT locale vide
        dht_recu = {
            "file1": ["peer1"],
            "file2": ["peer2"]
        }

        # Appel de la fonction
        merged_dht = merge_dht(dht_local, dht_recu)

        # La DHT locale doit être égale à la DHT reçue
        self.assertEqual(merged_dht, dht_recu)

    def test_merge_dht_conflict(self):
        # Données de test
        dht_local = {
            "file1": ["peer1"],
            "file2": ["peer2"]
        }
        dht_recu = {
            "file2": ["peer2", "peer3"],  # Un peer déjà présent
            "file3": ["peer4"]
        }

        # Appel de la fonction
        merged_dht = merge_dht(dht_local, dht_recu)

        # DHT attendue après la fusion
        expected_dht = {
            "file1": ["peer1"],
            "file2": ["peer2", "peer3"],  # La localisation 'peer2' ne doit pas être dupliquée
            "file3": ["peer4"]
        }

        # Vérification
        self.assertEqual(merged_dht, expected_dht)

if __name__ == "__main__":
    unittest.main()
"""