from flask import Flask, request, jsonify
from recup_ip import generate_key

app = Flask(__name__)

active_peers = []  # Liste des pairs actifs
files_storage = {} 

@app.route('/join', methods=['POST'])
def join_network():
    """
    Gestion de l'ajout d'un pair au réseau via une requête HTTP POST.
    curl -X POST http://127.0.0.1:5002/join -H "Content-Type: application/json" -d '{"ip": "192.168.1.2", "port": "6002"}'
    """
    data = request.get_json()
    ip = data.get("ip")
    port = data.get("port")

    if not ip or not port:
        return jsonify({"error": "IP et port requis"}), 400

    new_peer = (generate_key(f"{ip}:{port}"), ip, int(port))
    if new_peer not in active_peers:
        active_peers.append(new_peer)
        active_peers.sort(key=lambda peer: int(peer[0], 16))  # Trie en base 16
        new_peer_index = active_peers.index(new_peer)

        # Détermination des voisins
        if len(active_peers) == 1:
            neighbors = []
        elif len(active_peers) == 2:
            neighbors = [active_peers[(new_peer_index + 1) % len(active_peers)]]
        else:
            left_neighbor = active_peers[(new_peer_index - 1) % len(active_peers)]
            right_neighbor = active_peers[(new_peer_index + 1) % len(active_peers)]
            neighbors = [left_neighbor, right_neighbor]

        return jsonify({"message": "Ajouté au réseau", "neighbors": neighbors}), 200
    
    return jsonify({"error": "Pair déjà dans le réseau"}), 409


@app.route('/leave', methods=['POST'])
def leave_network():
    """
    Gestion du départ d'un pair du réseau via une requête HTTP POST.
    curl -X POST http://127.0.0.1:5002/leave -H "Content-Type: application/json" -d '{"ip": "192.168.1.2", "port": "6002"}'
    """
    data = request.get_json()
    ip = data.get("ip")
    port = data.get("port")

    if not ip or not port:
        return jsonify({"error": "IP et port requis"}), 400

    peer_to_remove = (generate_key(f"{ip}:{port}"), ip, int(port))
    if peer_to_remove in active_peers:
        active_peers.remove(peer_to_remove)
        return jsonify({"message": "Pair retiré du réseau"}), 200
    
    return jsonify({"error": "Pair non trouvé"}), 404


@app.route('/peers', methods=['GET'])
def get_active_peers():
    """
    Retourne la liste des pairs actifs.
    curl -X GET http://127.0.0.1:5002/peers  
    """
    return jsonify({"active_peers": active_peers}), 200

@app.route('/dht', methods=['GET'])
def get_dht():
    """
    Retourne la liste de dht.
    curl -X GET http://127.0.0.1:5002/dht  
    """
    return jsonify({"files_storage": files_storage}), 200

@app.route('/find_file', methods=['GET'])
def find_file():
    """
    Retourne la liste des pairs qui possèdent un fichier selon la clé donnée.
    curl -X GET "http://127.0.0.1:5002/find_file?file_key=abc123"

    """
    file_key = request.args.get("file_key")

    if not file_key:
        return jsonify({"error": "Clé de fichier requise"}), 400

    if file_key in files_storage:
        return jsonify({"peers": files_storage[file_key]}), 200
    else:
        return jsonify({"error": "Fichier non trouvé"}), 404

@app.route('/neighbors', methods=['GET'])
def get_neighbors():
    """
    Retourne les deux voisins les plus proches d'un pair donné (IP et port).
    curl -X GET "http://127.0.0.1:5002/neighbors?ip=192.168.1.2&port=6002"
    """
    ip = request.args.get("ip")
    port = request.args.get("port")

    if not ip or not port:
        return jsonify({"error": "IP et port requis"}), 400

    peer_key = generate_key(f"{ip}:{port}")
    peer = (peer_key, ip, int(port))

    if peer not in active_peers:
        return jsonify({"error": "Pair non trouvé"}), 404

    index = active_peers.index(peer)
    left_neighbor = active_peers[(index - 1) % len(active_peers)]
    right_neighbor = active_peers[(index + 1) % len(active_peers)]

    return jsonify({"left_neighbor": left_neighbor, "right_neighbor": right_neighbor}), 200


@app.route('/store_file', methods=['POST'])
def store_file():
    """
    Permet à un pair d'indiquer qu'il possède un fichier.
    curl -X POST http://127.0.0.1:5002/store_file -H "Content-Type: application/json" -d '{"ip": "192.168.1.2", "port": "6000", "file_key": "abc123"}'
    """
    data = request.get_json()
    ip = data.get("ip")
    port = data.get("port")
    file_key = data.get("file_key")

    if not ip or not port or not file_key:
        return jsonify({"error": "IP, port et clé de fichier requis"}), 400

    peer = (generate_key(f"{ip}:{port}"), ip, int(port))

    if peer not in active_peers:
        return jsonify({"error": "Pair non enregistré"}), 404

    if file_key not in files_storage:
        files_storage[file_key] = []

    if peer not in files_storage[file_key]:
        files_storage[file_key].append(peer)

    return jsonify({"message": "Fichier ajouté avec succès"}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
