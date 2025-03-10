import socket
import threading
import json
import time
import os
import sys
import shutil
import msgpack
from recup_ip import generate_key
from dht import assign_dht, request_dht, handle_dht, send_dht_local, create_add_file_message, create_looking_file_message, request_list_peer_have_file, send_replica_message, create_delete_file_message
from file_share import request_files, handle_files, wait_for_connection, get_free_port
from file_emplacement import add_file_to_network
from security import verify_pow, request_pow_verification

class PeerNode:
    def __init__(self, port):
        self.BOOTSTRAP_HOST = '127.0.0.1'
        self.BOOTSTRAP_PORT = 5001
        self.PEER_PORT = port
        self.REPLICA_MESSAGE = True
        self.active_peers = []  # Liste des pairs actifs
        self.my_node = [generate_key(f'127.0.0.1:{self.PEER_PORT}'), '127.0.0.1', self.PEER_PORT]
        self.dht_local = {}
        self.responsability_plage = None

    def bootstrap_interaction(self, action):
        """
        Fonction unique pour interagir avec le serveur Bootstrap pour se connecter (JOIN) ou quitter le réseau (LEAVE).
        """
        if action not in ['JOIN', 'LEAVE']:
            raise ValueError("Action non valide. Utilisez 'JOIN' ou 'LEAVE'.")

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.BOOTSTRAP_HOST, self.BOOTSTRAP_PORT))
                s.sendall(action.encode('utf-8'))

                if action == "JOIN":
                    response = s.recv(1024).decode('utf-8')
                    if response == "Send your listening port":
                        s.sendall(str(self.PEER_PORT).encode('utf-8'))
                    response = s.recv(1024).decode('utf-8')
                    self.active_peers = json.loads(response)
                    if not os.path.exists(f'.storage{self.PEER_PORT}'):
                        os.makedirs(f'.storage{self.PEER_PORT}')
                    return self.active_peers
                elif action == "LEAVE":
                    response = s.recv(1024).decode('utf-8')
                    self.attempt_peer_connections()
                    s.sendall(str(self.PEER_PORT).encode('utf-8'))
                    response = s.recv(1024).decode('utf-8')
                    if os.path.exists(f'.storage{self.PEER_PORT}'):
                        self.handle_leaving_storage()
                    shutil.rmtree(f'.storage{self.PEER_PORT}')
        except Exception as e:
            print(f"Erreur lors de l'interaction avec le Bootstrap ({action}) : {e}")
            shutil.rmtree(f'.storage{self.PEER_PORT}')
        if action == "LEAVE":
            sys.exit()

    def attempt_peer_connections(self):
        """
        Tentative de connexion à chaque pair actif
        """
        if len(self.active_peers) < 1:
            return
        for peer in self.active_peers:
            peer_ip, peer_port = peer[1:]
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((peer_ip, peer_port))
                    message = {"action": "Connection with the peer", "data": [self.my_node, self.active_peers]}
                    s.sendall(msgpack.packb(message))
            except Exception as e:
                print(f"Peer connection error {peer_ip}:{peer_port} : {e}")

    def handle_leaving_storage(self):
        """
        Traite les fichiers stockés avant de quitter le réseau.
        """
        for f in os.listdir(f'.storage{self.PEER_PORT}'):
            if os.path.isfile(os.path.join(f'.storage{self.PEER_PORT}', f)):
                key = os.path.splitext(f)[0]
                data = create_delete_file_message(key, self.my_node)
                send_replica_message(self.my_node, [self.active_peers[1]], key)
                REPLICA_MESSAGE = True
                event = threading.Event()
                thread = threading.Thread(target=wait_for_connection_event, args=(event,))
                thread.start()
                event.wait(timeout=10)
                while REPLICA_MESSAGE is False:
                    REPLICA_MESSAGE = wait_for_connection()
                message = {"action": "delete_peer_dht", "data": data}
                self.dht_local = handle_dht(self.my_node, self.active_peers, message, self.dht_local, self.responsability_plage)

    def start_peer_server(self):
        """
        Lance un serveur destiné à accepter/gérer les connexions entre pairs déjà connectés au réseau
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', self.PEER_PORT))
        server_socket.listen(5)
        print(f"Peer server started, listening on port {self.PEER_PORT}")
        
        while True:
            conn, addr = server_socket.accept()
            self.handle_communication_between_peer(conn)

    def handle_communication_between_peer(self, conn):
        """
        Gère la communication entre 2 pairs.
        """
        try:
            data = msgpack.unpackb(conn.recv(1024))
            if data.get("action") == "Connection with the peer":
                self.add_neighbor_peer(data)
            elif data.get("action") == "request_file":
                self.handle_files(data)
            elif data.get("action") in ["request_dht", "add_file", "send_dht", "delete_peer_dht"]:
                self.dht_local = handle_dht(self.my_node, self.active_peers, data, self.dht_local, self.responsability_plage)
            elif data.get("action") == "looking_file":
                self.request_list_peer_have_file(data)
        except Exception as e:
            print(f"Peer management error: {e}")
        finally:
            conn.close()

    def add_neighbor_peer(self, data):
        """
        Ajoute un pair voisin à la liste active_peers.
        """
        if data.get("action") == "Connection with the peer":
            peer_info = data["data"]
            self.active_peers.extend(peer_info)

    def handle_files(self, data):
        """
        Gère la demande de fichiers.
        """
        key = data.get("data").get("key")
        handle_files(data, f'.storage{self.PEER_PORT}')
        self.dht_local = handle_dht(self.my_node, self.active_peers, data, self.dht_local, self.responsability_plage)

    def request_list_peer_have_file(self, data):
        """
        Gère la demande de fichiers disponibles auprès des pairs.
        """
        key = data.get("data").get("key")
        request_list_peer_have_file(self.my_node, self.active_peers, data, self.dht_local, self.responsability_plage)

    def add_file_to_network(self, file, storage_directory):
        """
        Ajoute un fichier au réseau.
        """
        file_coder, key = create_add_file_message(file, self.my_node)
        if request_pow_verification(self.active_peers, key, self.my_node, 2):
            add_file_to_network(file, storage_directory)
            time.sleep(1)
            send_replica_message(self.my_node, self.active_peers, key)
            data = {"action": "add_file", "data": file_coder}
            self.dht_local = handle_dht(self.my_node, self.active_peers, data, self.dht_local, self.responsability_plage)

# Exemple d'utilisation :
# Si vous utilisez un serveur web comme Flask ou FastAPI, vous pourriez faire ceci :

# from fastapi import FastAPI

# app = FastAPI()
# peer_node = PeerNode(5000)

# @app.get("/join_network")
# def join_network():
#     active_peers = peer_node.bootstrap_interaction("JOIN")
#     return {"message": "Joined network", "active_peers": active_peers}

# @app.get("/leave_network")
# def leave_network():
#     peer_node.bootstrap_interaction("LEAVE")
#     return {"message": "Left network"}

# @app.post("/add_file")
# def add_file(file: str):
#     peer_node.add_file_to_network(file, f'.storage{peer_node.PEER_PORT}')
#     return {"message": "File added"}

