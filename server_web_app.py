import os
import threading
import requests
from flask import Flask, request, jsonify, send_file, Response
import socket 
import logging
import random
import mimetypes
from flask_cors import CORS
import zipfile
from recup_ip import generate_key
from io import BytesIO

logging.basicConfig(level=logging.DEBUG)

UPLOAD_FOLDER = "uploads"
BOOTSTRAP_URL = "http://192.168.80.3:5002"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
CORS(app)


def is_port_open(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((ip, port)) == 0
    

@app.route('/download_server_start', methods=['GET'])
def download_files():
    """
    curl -X GET http://172.31.190.86:5003/download_server_start -o server_files.zip
    """
    zip_filename = "server_files.zip"
    
    # Chemins des fichiers à inclure
    files_to_include = ["start_server.bat", "peer_server.py"]
    
    # Création du fichier ZIP
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for file in files_to_include:
            if os.path.exists(file):
                zipf.write(file)

    # Envoi du fichier ZIP
    return send_file(zip_filename, as_attachment=True)


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    curl -X POST -F "file=@mon_fichier.txt" http://192.168.80.32:5003/upload
    """
    # Vérifier si un fichier a été envoyé
    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier envoyé"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nom de fichier invalide"}), 400
    file_extension = os.path.splitext(file.filename)[1]
    # Lire le contenu du fichier
    file_content = file.read()

    # Générer la clé unique (hash du fichier)
    file_key = generate_key(str(file_content))

    # Envoi de la requête pour stocker le fichier
    store_url = f"{BOOTSTRAP_URL}/store_file"
    payload = {"file_key": file_key, "file_name" : file.filename}
    headers = {"Content-Type": "application/json"}
    if request.form.get("password") :
        password = request.form.get("password")
        payload["password"] = password

    try:
        response = requests.post(store_url, json=payload, headers=headers, verify=False)
        response_data = response.json()

        # Vérifier si on a bien une liste de pairs responsables
        responsible_peers = response_data.get("responsible_peers", [])
        if not responsible_peers:
            return jsonify({"error": "Aucun pair responsable trouvé"}), 500
        file_extension = os.path.splitext(file.filename)[1]
        # Envoyer le fichier à chaque pair responsable
        file_name = file_key + file_extension
        for peer in responsible_peers:
            peer_id, peer_ip, peer_port = peer
            peer_upload_url = f"http://{peer_ip}:{peer_port}/upload"
            
            print(file_name)
            files = {'file': (file_name, file_content)}
            data = {'file_key': file_key}
            try:
                upload_response = requests.post(peer_upload_url, files=files, data = data)
                print(f"Upload vers {peer_ip}:{peer_port} -> {upload_response.status_code}")
            except requests.RequestException as e:
                print(f"Erreur en envoyant à {peer_ip}:{peer_port}: {e}")

        return jsonify({"message": "Fichier envoyé avec succès", "responsible_peers": responsible_peers}), 200

    except requests.RequestException as e:
        return jsonify({"error": f"Erreur de communication avec /store_file: {str(e)}"}), 500

@app.route('/download', methods=['GET'])
def download_file():
    """
    curl -X POST -F "file=@mon_fichier.txt" http://192.168.80.32:5003/upload
    """
    file_key = request.args.get("file_key")
    print(file_key)
    if not file_key:
        return jsonify({"error": "Nom du fichier requis"}), 400

    response = requests.get(f"{BOOTSTRAP_URL}/find_file", params={"file_key": file_key})
    app.logger.debug(f"Réponse de find_file: {response.status_code} - {response.text}")

    if response.status_code != 200:
        return jsonify({"error": "Fichier non trouvé sur le réseau"}), 404

    peers = response.json().get("peers",[])
    print(peers)
    if not peers:
        return jsonify({"error": "Aucun pair ne possède ce fichier"}), 404

    for peer in peers:
        print(peer)
        peer_ip = peer.get("ip")
        peer_port = peer.get("port")
        try:
            file_url = f"http://{peer_ip}:{peer_port}/download/{file_key}"
            file_response = requests.get(file_url, stream=True, timeout=60)
            if file_response.status_code == 200:
                # Récupérer le nom du fichier depuis Content-Disposition
                original_filename = file_response.headers.get("Content-Disposition")
                if original_filename:
                    original_filename = original_filename.split("filename=")[-1].strip('"')
                    extension = "." + original_filename.split(".")[-1]  # Extraire l'extension
                else:
                    # Essayer de deviner l'extension depuis Content-Type
                    content_type = file_response.headers.get("Content-Type", "")
                    extension = mimetypes.guess_extension(content_type) or ""

                # Construire le nom du fichier final avec l'extension
                local_filename = f"fichier_telecharge{extension}"
                file_data = BytesIO(file_response.content)

                # Envoyer le fi chier avec le bon nom et la bonne extension
                return send_file(
                    file_data,
                    as_attachment=True,
                    download_name=local_filename,
                    mimetype=file_response.headers.get("Content-Type", "application/octet-stream")
                )

                
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Erreur avec {peer_ip}:{peer_port} - {e}")
    return jsonify({"error": "Impossible de récupérer le fichier"}), 404

 
@app.route('/api/ip', methods=['GET']) # AutoRemplissage ip
def get_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return jsonify({"message": "Rejoint avec succès", "ip": request.remote_addr})
 
@app.route('/list_dht', methods=['GET'])
def list_dht():
    response = requests.get(f"{BOOTSTRAP_URL}/list_dht")
    response_data = response.json()
    list_file_storage = response_data.get('list_files_storage')
    return jsonify({"list_files_storage": list_file_storage}), 200

@app.route('/info', methods=['GET'])
def info():
    response = requests.get(f"{BOOTSTRAP_URL}/info")
    response_data = response.json()
    nombre_fichier = response_data.get('nombre_fichier')
    nombre_noeud =response_data.get('nombre_noeud')
    return jsonify({"nombre_fichier": nombre_fichier ,"nombre_noeud" : nombre_noeud}), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5003)
