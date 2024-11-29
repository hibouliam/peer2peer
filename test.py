import socket
import threading
import json
import sys
from recup_ip import generate_key
import msgpack
from dht import assign_dht, request_dht, handle_dht

BOOTSTRAP_HOST = '127.0.0.1'  # Adresse du serveur bootstrap
BOOTSTRAP_PORT = 5001  # Port du bootstrap
PEER_PORT = 7002  # Port d'écoute du pair

active_peers = []  # Liste des pairs actifs
my_node = [generate_key(f'127.0.0.1:{PEER_PORT}'), '127.0.0.1', PEER_PORT]
dht_local = {"12378"}
responsability_plage = None


def bootstrap_interaction(action: str, active_peers: list) -> list:
    if action not in ['JOIN', 'LEAVE']:
        print("Action non valide. Utilisez 'JOIN' ou 'LEAVE'.")
        return []

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((BOOTSTRAP_HOST, BOOTSTRAP_PORT))
            s.sendall(action.encode('utf-8'))

            if action == "JOIN":
                response = s.recv(1024).decode('utf-8')
                if response == "Send your listening port":
                    s.sendall(str(PEER_PORT).encode('utf-8'))
                response = s.recv(1024).decode('utf-8')
                active_peers = json.loads(response)
                return active_peers

            elif action == "LEAVE":
                s.sendall(str(PEER_PORT).encode('utf-8'))
                response = s.recv(1024).decode('utf-8')
                print(f"Réponse reçue du Bootstrap : {response}")
    except Exception as e:
        print(f"Erreur lors de l'interaction avec le Bootstrap ({action}) : {e}")

    if action == "LEAVE":
        sys.exit()
    return []


def start_peer_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', PEER_PORT))
    server_socket.listen(5)
    print(f"Peer server started, listening on port {PEER_PORT}")

    while True:
        conn, addr = server_socket.accept()
        print(f"Incoming connection from {addr}")
        handle_communication_between_peer(conn)


def handle_communication_between_peer(conn):
    global dht_local
    global responsability_plage
    try:
        data = msgpack.unpackb(conn.recv(1024))
        add_neighbor_peer(data, my_node, active_peers, responsability_plage)
        dht_local = handle_dht(my_node, active_peers, data, dht_local, responsability_plage)
        responsability_plage = assign_dht(my_node, active_peers)
    except Exception as e:
        print(f"Peer management error : {e}")
    finally:
        conn.close()


def attempt_peer_connections(my_node: list):
    if len(active_peers) < 1:
        return
    for peer in active_peers:
        peer_ip, peer_port = peer[1:]
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((peer_ip, peer_port))
                message = {"action": "Connection with the peer", "data": [my_node, active_peers]}
                s.sendall(msgpack.packb(message))
        except Exception as e:
            print(f"Peer connection error {peer_ip}:{peer_port} : {e}")


def add_neighbor_peer(data: str, my_node: list, active_peers: list, responsability_plage: tuple) -> None:
    try:
        if data.get("action") == "Connection with the peer":
            peer_info = data["data"]
            peer_info = applatir_données(peer_info)
            if len(active_peers) <= 1:
                active_peers.append(peer_info[0])
            else:
                count = 0
                for peer in peer_info:
                    if peer[1:] != ['127.0.0.1', PEER_PORT]:
                        if peer in active_peers:
                            if count == 0:
                                count += 1
                                active_peers.remove(peer)
                            else:
                                request_dht(my_node, active_peers, responsability_plage)
                                return
                        else:
                            active_peers.append(peer)
    except Exception as e:
        print(f"Erreur lors de l'ajout d'un pair voisin : {e}")


def applatir_données(data: list) -> list:
    result = []
    for item in data:
        if isinstance(item[0], list):
            result.extend(item)
        else:
            result.append(item)
    return result


def main():
    global active_peers
    global responsability_plage

    try:
        while True:
            print("\nActions disponibles :")
            print("1. Tapez 'j' pour rejoindre le réseau.")
            print("2. Tapez 'q' pour quitter le réseau.")
            
            action = input("Votre choix : ").lower()

            if action == 'j':
                active_peers = bootstrap_interaction("JOIN", active_peers)
                if not active_peers:
                    print("Impossible de rejoindre le réseau.")
                    continue

                server_thread = threading.Thread(target=start_peer_server)
                server_thread.daemon = True
                server_thread.start()

                attempt_peer_connections(my_node)
                responsability_plage = assign_dht(my_node, active_peers)
                request_dht(my_node, active_peers, responsability_plage)

                print("Plage de responsabilité :", responsability_plage)
                print("Liste des pairs actifs :", active_peers)

            elif action == 'q':
                bootstrap_interaction("LEAVE", active_peers)
                break
            else:
                print("Choix non valide. Veuillez taper 'j' ou 'q'.")
    except KeyboardInterrupt:
        print("\nInterruption par l'utilisateur. Déconnexion en cours...")
        bootstrap_interaction("LEAVE", active_peers)


if __name__ == "__main__":
    main()
