from flask import Flask, request, jsonify, send_from_directory
import os 
import requests
from flask_cors import CORS
import atexit
import subprocess
import time
import socket
app = Flask(__name__)
CORS(app)
BOOTSTRAP_URL = "http://192.168.80.3:5002"
API_URL ="https://6c1a-78-243-97-162.ngrok-free.app"
# Dossier de stockage des fichiers
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def get_local_ip() -> str:
    try:
        # Crée une connexion UDP temporaire pour déterminer l'IP locale
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Utilise une IP externe pour déterminer l'IP locale
            local_ip = s.getsockname()[0]
    except Exception:
        print("pro")
        local_ip = "Impossible de récupérer l'adresse IP locale"
    return local_ip

IP = get_local_ip()
# Fonction pour envoyer une requête POST lors du démarrage
def notify_join():
    try:

        data = {"ip": IP, "port": "5000"}

        # Envoi de la requête POST avec les données JSON
        response = requests.post(f"{BOOTSTRAP_URL}/join", json=data)
        print(f"Requête join envoyée avec succès: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'envoi de la requête join: {e}")

# Fonction pour envoyer une requête POST lors de l'arrêt
def notify_leave():
    
    try:
        for file_name in os.listdir(app.config["UPLOAD_FOLDER"]):
            time.sleep(2)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], file_name)
            if os.path.isfile(file_path):
                try:
                    # Utilisation de requests pour envoyer le fichier
                    with open(file_path, 'rb') as f:
                        files = {'file': (file_name, f)}  # Forme multipart pour envoyer le fichier
                        upload_url = f"{API_URL}/upload"  
                        headers = {
                            "ngrok-skip-browser-warning": "true"
                        }
                        upload_response = requests.post(upload_url, files=files,headers=headers)
                        if upload_response.status_code == 200:
                            print(f"Fichier {file_name} téléchargé avec succès.")
                        else:
                            print(f"Erreur lors de l'envoi du fichier {file_name}: {upload_response.status_code}")

                    # Supprimer le fichier après le téléchargement
                    os.remove(file_path)
                    print(f"Fichier {file_name} supprimé avec succès.")
                except requests.exceptions.RequestException as e:
                    print(f"Erreur lors de l'envoi de la requête leave: {e}")

        try :
            time.sleep(2)
            data = {"ip": IP, "port": "5000"}
            response = requests.post(f"{BOOTSTRAP_URL}/leave", json=data)
            print(f"Requête leave envoyée avec succès: {response.status_code}")
            time.sleep(2)
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de l'envoi de la requête leave: {e}")
        
        
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'envoi de la requête leave: {e}")

@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Permet d'envoyer un fichier au serveur.
    Usage : curl -X POST -F "file=@chemin_du_fichier" http://127.0.0.1:5002/upload
    """
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier envoyé"}), 400
    
    file = request.files["file"]

    # Vérifier si le fichier a un nom valide
    if file.filename == "":
        return jsonify({"error": "Nom de fichier invalide"}), 400
    

    # Sauvegarder le fichier dans le répertoire spécifié
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))
    local_ip = IP
    port= "5000"
    file_key= os.path.splitext(file.filename)[0]

    url = f"{BOOTSTRAP_URL}/add_dht?file_name={file_key}&ip={local_ip}&port={port}"

    # Effectuez la requête GET
    try:
        response = requests.get(url)
        
        # Vérifiez la réponse
        if response.status_code == 200:
            print("Fichier ajouté avec succès à la DHT.")
        else:
            print(f"Erreur lors de l'ajout du fichier : {response.json()}")

        return jsonify({"message": f"Fichier {file.filename} envoyé avec succès"}), 200
    except requests.RequestException as e:
        print(f"Erreur lors de l'envoi de la requête : {e}")

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    """
    Permet de télécharger un fichier du serveur.
    Usage : curl -X GET http://127.0.0.1:5000/download/20221129_145533.mp4 -o fichier_sauvegarde
    """
    folder = app.config["UPLOAD_FOLDER"]
    file_found = None
    
    # Parcourir les fichiers dans le répertoire et chercher celui qui commence par le même nom
    for file in os.listdir(folder):
        if file.startswith(filename):
            file_found = file
            break
    
    try:
        return send_from_directory(app.config["UPLOAD_FOLDER"], file_found, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "Fichier non trouvé"}), 404


@app.route("/files", methods=["GET"])
def list_files():
    """
    Retourne la liste des fichiers disponibles.
    Usage : curl -X GET http://127.0.0.1:5000/files
    """
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    return jsonify({"files": files})

import signal


# Fonction pour gérer proprement l'arrêt
def graceful_shutdown(signal, frame):
    print("\n🔴 Arrêt détecté. Exécution de notify_leave() avant fermeture...")
    notify_leave()  # Exécuter la fonction de nettoyage
    print("✅ Nettoyage terminé. Arrêt du serveur Flask.")
    os._exit(0)  # Forcer l'arrêt propre après le nettoyage

# Associer la fonction à SIGINT (Ctrl+C) et SIGTERM (kill)
signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)

if __name__ == "__main__":
    
    notify_join()  # Fonction d'initialisation avant l'exécution du serveur
    app.run(host="0.0.0.0", port=5000, debug=True)
 