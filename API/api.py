from flask import Flask, request,jsonify
from flask_cors import CORS
import os
import socket

app = Flask(__name__)
CORS(app)

# Répertoire où les fichiers seront sauvegardés
UPLOAD_FOLDER = "static/files"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Crée le répertoire s'il n'existe pas
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



@app.route('/api/ip', methods=['GET'])
def get_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return jsonify({"ip": request.remote_addr})
    # return jsonify({"ip": ip_address})  # Retourne l'adresse IP locale


if __name__ == "__main__":
    app.run(debug=True)
