from flask import Flask, request, jsonify
from recup_ip import generate_key
from dht import determine_responsibility, assign_dht
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
active_peers = []  # Liste des pairs actifs
files_storage = {} 
list_file_storage = {}
passwords = {}

@app.route('/join', methods=['POST'])
def join_network():
    """
    Gestion de l'ajout d'un pair au réseau via une requête HTTP POST.
    curl -X POST http://192.168.4.3:5002/join -H "Content-Type: application/json" -d '{"ip": "192.168.1.2", "port": "6002"}'
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
    print(ip,port)
    for file_name, peers in list(files_storage.items()):
        # On vérifie si l'IP et le port existent dans la liste des pairs pour ce fichier
        for peer in peers:
            if peer.get("ip") == ip :
                peers.remove(peer)  # Supprimer le pair de la liste

        # Si plus de pairs ne sont associés au fichier, on le supprime de files_storage
        if not peers:
            file_key = files_storage.get(file_name)
            del files_storage[file_name]
            del passwords[file_key]
            for value, key in list(list_file_storage.items()):
                if key == file_key:  # Si la valeur correspond à `file_name`
                    del list_file_storage[key]  # Supprimer la clé (le file_name)
                    print(f"{file_name} a été supprimé de list_files_storage")
                    break

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

@app.route('/list_dht', methods=['GET'])
def get_list_dht():
    """
    Retourne la liste de dht.
    curl -X GET http://127.0.0.1:5002/dht  
    """
    return jsonify({"list_files_storage": list_file_storage}), 200

@app.route('/list_passwords', methods=['GET'])
def get_list_passwords():
    """
    Retourne la liste de dht.
    curl -X GET http://127.0.0.1:5002/dht  
    """
    return jsonify({"list_passwords": passwords}), 200

@app.route('/info', methods=['GET'])
def info():
    """
    Retourne la liste de dht.
    curl -X GET http://127.0.0.1:5002/dht  
    """
    return jsonify({"nombre_fichier": len(files_storage) , "nombre_noeud" : len(active_peers)}), 200

@app.route('/find_file', methods=['GET'])
def find_file():
    """
    Retourne la liste des pairs qui possèdent un fichier selon la clé donnée.
    curl -X GET "http://192.168.80.32:5002/find_file?file_key=abc123"

    """
    file_key = request.args.get("file_key")

    if not file_key:
        return jsonify({"error": "Clé de fichier requise"}), 400

    if file_key in files_storage:
        return jsonify({"peers": files_storage[file_key]}), 200
    else:
        return jsonify({"error": "Fichier non trouvé"}), 404
@app.route('/add_dht', methods=['GET'])
def add_dht():
    """
    Cette fonction ajoute un fichier à la table DHT avec le file_name, l'ip et le port reçus.
    Si le fichier existe déjà dans la table DHT, on y ajoute la nouvelle IP et le port à la liste des pairs.
    Usage: curl -X GET "http://192.168.80.32:5002/add_dht?file_name=mon_fichier.txt&ip=192.168.1.10&port=5000"
    """
    # Récupérer les paramètres de la requête GET
    file_name = request.args.get("file_name")
    ip = request.args.get("ip")
    port = request.args.get("port")
    
    # Vérifier si tous les paramètres sont fournis
    if not file_name or not ip or not port:
        return jsonify({"error": "Paramètres manquants, veuillez fournir file_name, ip et port."}), 400
    
    # Si le fichier existe déjà dans la table DHT, on ajoute l'IP et le port à la liste des pairs
    if file_name in files_storage:
        # Vérifier si l'IP et le port sont déjà associés à ce fichier
        if {"ip": ip, "port": port} not in files_storage[file_name]:
            files_storage[file_name].append({"ip": ip, "port": port})
            message = f"IP {ip} et port {port} ajoutés au fichier {file_name}"
        else:
            message = f"Le pair (IP: {ip}, Port: {port}) est déjà associé au fichier {file_name}"
    else:
        # Si le fichier n'existe pas encore, on l'ajoute avec l'IP et le port
        files_storage[file_name] = [{"ip": ip, "port": port}]
        message = f"Fichier {file_name} ajouté avec IP {ip} et Port {port} à la DHT"

    # Retourner un message de succès
    return jsonify({"message": message}), 200

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
    Permet savoir qui doit stocker le fichier.
    curl -X POST http://192.168.80.32:5002/store_file -H "Content-Type: application/json" -d '{"ip": "192.168.1.2", "port": "6000", "file_key": "abc123"}'
    """
    data = request.get_json()
    file_key = data.get("file_key")
    file_name = data.get("file_name")

    if file_key not in list_file_storage.values():
        if data.get("password") :
            passwords[file_key] = data.get("password")
        original_name = file_name
        count = 1
        
        # Vérifier si file_name existe déjà avec un autre file_key
        while file_name in list_file_storage:
            if list_file_storage[file_key] == file_key:
                print(f"{file_name} existe déjà avec la même file_key, pas d'ajout")
                return
            file_name = f"{original_name} ({count})"
            count += 1
        
        # Ajouter le fichier avec un nom unique
        
        list_file_storage[file_name] = file_key
    
    if len(active_peers) <= 3:
        return jsonify({
            "message": "Fichier ajouté avec succès",
            "responsible_peers": active_peers
        }), 200

    file_key_int = int(file_key, 16)

    for i, peer in enumerate(active_peers):
        left_responsibility, right_responsibility = assign_dht(peer, active_peers)

        # Gérer le cas où right_responsibility est None
        if right_responsibility is None:
            right_responsibility = float('inf')  # Définit un maximum pour inclure toutes les valeurs

        print(left_responsibility, right_responsibility)

        if left_responsibility <= file_key_int <= right_responsibility:
            peer_send = [
                active_peers[i],
                active_peers[(i + 1) % len(active_peers)],
                active_peers[(i + 2) % len(active_peers)]
            ]
            return jsonify({
                "message": "Fichier ajouté avec succès",
                "responsible_peers": peer_send
            }), 200

    # Si aucun peer responsable n'a été trouvé
    return jsonify({"error": "Aucun pair responsable trouvé"}), 500


def get_responsible_peers(file_key_hash: int, active_peers: list) -> list:
    """
    Retourne la liste des pairs responsables du fichier en fonction de la clé du fichier.
    Utilise la DHT et la fonction d'assignment pour déterminer les pairs responsables.
    """
    responsible_peers = []
    
    for peer in active_peers:
        peer_key = int(peer[0], 16)  # Clé du pair, récupérée à partir de son identifiant hashé
        left_responsibility, right_responsibility = assign_dht(peer, active_peers)
        
        # Vérifier si la clé du fichier appartient à la plage de responsabilité du pair
        if (left_responsibility is None or file_key_hash >= left_responsibility) and \
           (right_responsibility is None or file_key_hash < right_responsibility):
            responsible_peers.append(peer)
    
    return responsible_peers

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
