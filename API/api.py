from flask import Flask, request,jsonify
from flask_cors import CORS
import os
import socket
import threading
import shutil
import time,random
from recup_ip import generate_key
# from bootstrap import process_peer_connection
from conn_bootstrap import bootstrap_interaction, add_file_to_network,create_add_file_message,send_replica_message,handle_dht,attempt_peer_connections,request_dht,start_peer_server,assign_dht

app = Flask(__name__)
CORS(app)

BOOTSTRAP_HOST = '127.0.0.1'  # Adresse du serveur bootstrap
BOOTSTRAP_PORT = 5001     # Port du bootstrap
# PEER_PORT = 7013     # Port d'écoute du pair
# PEER_PORT = None
# PEER_PORT = random.randint(1024,65535)

active_peers = []  # Liste des pairs actifs
# my_node=[generate_key(f'127.0.0.1:{PEER_PORT}'),'127.0.0.1',PEER_PORT]
dht_local = {}
responsability_plage = None


# Répertoire où les fichiers seront sauvegardés
# UPLOAD_FOLDER = "static/files"
# Définition des dossiers
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")

# Assurez-vous que les dossiers existent
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


# Crée le répertoire s'il n'existe pas
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "Pas de fichier envoyé", 400

    file = request.files["file"]

    if file.filename == "":
        return "Aucun fichier sélectionné", 400

    file.save(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))
    return "Fichier sauvegardé avec succès", 200


@app.route('/api/download', methods=['POST'])
def download_file():
    try:
        # Récupération du nom de fichier depuis la requête
        data = request.get_json()
        filename = data.get("filename")

        if not filename:
            return jsonify({"error": "Le nom du fichier est requis"}), 400

        # Chemin complet du fichier source et destination
        source_path = os.path.join(UPLOAD_FOLDER, filename)
        dest_path = os.path.join(DOWNLOAD_FOLDER, filename)

        # Vérifier si le fichier existe dans 'uploads'
        if not os.path.exists(source_path):
            return jsonify({"error": "Fichier non trouvé dans le dossier uploads"}), 404

        # Copier le fichier dans 'downloads'
        shutil.copy(source_path, dest_path)

        return jsonify({"message": f"Fichier {filename} téléchargé dans downloads avec succès"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/ip', methods=['GET'])
def get_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    # bootstrap_interaction(action="JOIN", active_peers = active_peers) #rejoindre le réseau
    # if active_peers is None:
    #     return jsonify({"error": "Impossible de récupérer la liste des pairs"}), 500
    return jsonify({"message": "Rejoint avec succès", "active_peers": active_peers,"ip": request.remote_addr})

@app.route('/join', methods=['POST'])
def join_network():
    global active_peers, dht_local, responsability_plage
   
    # Récupérer le port depuis la requête
    PEER_PORT = request.json.get("port", random.randint(1024, 65535))
    # PEER_PORT = random.randint(1024,65535),
    my_node=[generate_key(f'127.0.0.1:{PEER_PORT}'),'127.0.0.1',PEER_PORT]
    print("PEER PORT :" , PEER_PORT)
    active_peers = bootstrap_interaction("JOIN", active_peers)  # Joindre le réseau
    # Démarrer le serveur peer
    server_thread = threading.Thread(target=start_peer_server)
    server_thread.daemon = True
    server_thread.start()
    # Tentative de connexion aux pairs
    attempt_peer_connections(my_node)
    responsability_plage = assign_dht(my_node, active_peers)
    request_dht(my_node, active_peers, responsability_plage)

    print("active_peers :" , active_peers)
    print("Plage de responsabilité :", responsability_plage)
    print("Liste des pairs actifs :", active_peers)
    print("dht local :",dht_local)

    return jsonify({"status": "success", "message": "Joined network successfully!"}), 200
    
@app.route('/leave', methods=['POST'])
def leave():
    try:
        bootstrap_interaction("LEAVE", active_peers)
        return jsonify({"message": "Déconnexion du réseau"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/print', methods=['GET'])
def print_node():
    # Retourne les informations du noeud
    print("Plage de responsabilité :", responsability_plage)
    print("Liste des pairs actifs :", active_peers)
    print("dht local :",dht_local)

    return jsonify({
         "active_peers": active_peers,
         "dht_local": dht_local,
         "responsability_plage": responsability_plage
    })
    

@app.route('/api/files', methods=['GET'])
def list_files():
    # time.sleep(5)
    try:
        # Liste tous les fichiers dans le dossier "uploads"
        files = os.listdir(UPLOAD_FOLDER)
        return jsonify({"files": files}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Par défaut, le port est 5000
    app.run(debug=True,host="0.0.0.0", port=port)

