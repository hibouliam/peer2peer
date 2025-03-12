import os
import threading
import requests
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
BOOTSTRAP_SERVER = "http://127.0.0.1:5002"  # Adresse du serveur Bootstrap

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)  # Créer le dossier s'il n'existe pas

def start_flask_app(ip, port):

    thread = threading.Thread(target=lambda: app.run(host=ip, port=port, debug=True, use_reloader=False))
    thread.start()

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Permet à un pair d'uploader un fichier.
    Enregistre le fichier localement et notifie le réseau qu'il le possède.
    """
    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier envoyé"}), 400

    file = request.files['file']
    ip = request.form.get("ip")  # IP du pair
    port = request.form.get("port")  # Port du pair
    start_flask_app(ip, port)  # Démarrer le serveur Flask si ce n'est pas déjà fait    
    if not ip or not port:
        return jsonify({"error": "IP et port requis"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)  # Sauvegarde du fichier

    # Notifier le Bootstrap
    file_key = file.filename  # Utilisation du nom du fichier comme clé
    response = requests.post(
        f"{BOOTSTRAP_SERVER}/store_file",
        json={"ip": ip, "port": int(port), "file_key": file_key}
    )

    return jsonify({"message": "Fichier uploadé avec succès", "response": response.json()}), response.status_code



@app.route('/download', methods=['GET'])
def download_file():
    """
    Permet de télécharger un fichier en demandant aux pairs qui le possèdent.
    curl -X GET "http://127.0.0.1:5003/download?file_key=mon_fichier.txt" -o mon_fichier.txt

    """
    file_key = request.args.get("file_key")
    if not file_key:
        return jsonify({"error": "Nom du fichier requis"}), 400

    # Demande au Bootstrap quels pairs ont ce fichier
    response = requests.get(f"{BOOTSTRAP_SERVER}/find_file", params={"file_key": file_key})
    if response.status_code != 200:
        return jsonify({"error": "Fichier non trouvé sur le réseau"}), 404

    peers = response.json().get("peers", [])
    if not peers:
        return jsonify({"error": "Aucun pair ne possède ce fichier"}), 404

    # Essayer de récupérer le fichier chez un des pairs
    for peer in peers:
        peer_ip, peer_port = peer[1], peer[2]
        try:
            file_url = f"http://{peer_ip}:{peer_port}/files/{file_key}"
            file_response = requests.get(file_url, stream=True)

            if file_response.status_code == 200:
                local_path = os.path.join(UPLOAD_FOLDER, file_key)
                with open(local_path, 'wb') as f:
                    for chunk in file_response.iter_content(1024):
                        f.write(chunk)

                return send_file(local_path, as_attachment=True)

        except requests.exceptions.RequestException:
            continue  # Essayer le prochain pair en cas d'échec

    return jsonify({"error": "Impossible de récupérer le fichier"}), 500


@app.route('/files/<filename>', methods=['GET'])
def serve_file(filename):
    """
    Permet de servir un fichier stocké localement pour un autre pair.
    """
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)

    return jsonify({"error": "Fichier introuvable"}), 404


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5003, debug=True)
