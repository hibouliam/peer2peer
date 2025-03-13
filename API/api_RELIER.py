from flask import Flask, request,jsonify
from flask_cors import CORS
import threading,sys,random,socket,time
from recup_ip import generate_key
import msgpack
import os
from dht import assign_dht, request_dht,handle_dht, send_dht_local,create_add_file_message, create_looking_file_message, request_list_peer_have_file, send_replica_message,create_delete_file_message
from file_share import request_files,handle_files
from file_emplacement import add_file_to_network
# from sans_global import bootstrap_interaction,attempt_peer_connections,start_peer_server,handle_communication_between_peer,add_neighbor_peer,applatir_données
from variable import create_variable_json, update_or_add_variable, load_variable_json
from conn_bootstrap import bootstrap_interaction,attempt_peer_connections,start_peer_server,handle_communication_between_peer,add_neighbor_peer,applatir_données
from security import verify_pow, request_pow_verification  

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

active_peers = []
dht_local = {}
lock = threading.Lock()


@app.route('/api/ip', methods=['GET']) # AutoRemplissage ip
def get_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    # bootstrap_interaction(action="JOIN", active_peers = active_peers) #rejoindre le réseau
    # if active_peers is None:
    #     return jsonify({"error": "Impossible de récupérer la liste des pairs"}), 500
    return jsonify({"message": "Rejoint avec succès", "active_peers": active_peers,"ip": request.remote_addr})

@app.route("/join", methods=["POST"])
def join_network():
    global active_peers
    # global active_peers,responsability_plage
    data = request.json
    print(data)
    port = int(data.get("peer_port"))
    print("PORT : ", port,type(port))
    # my_node = [generate_key(f'127.0.0.1:{port}'),'127.0.0.1',port]

    active_peers = bootstrap_interaction(action = "JOIN",peer_port=port)  # Tester l'action JOIN
    print("[DEBUG] Ligne Join est passé")
    server_thread = threading.Thread(target=start_peer_server, args=(port,)) # Création d'un thread pour gérer la connexion entre 2 pairs avec la fonction start_peer_server
    print("[DEBUG] serveur thread fixé")
    server_thread.daemon = True
    print("[DEBUG] serveur thread daemon true")
    server_thread.start()
    print("[DEBUG] serveur thread started")

    dht_local = load_variable_json(port, "dht" )
    responsability_plage = load_variable_json(port, "responsability_plage" )
    active_peers = load_variable_json(port, "active_peers" )
    my_node = load_variable_json(port, "my_node" )


     # Se connecter aux autres pairs du réseau
    attempt_peer_connections(my_node,active_peers=active_peers)
    responsability_plage=assign_dht(my_node, active_peers)
    request_dht(my_node, active_peers, responsability_plage)
    update_or_add_variable(port, "responsability_plage", responsability_plage)
            
    # with lock:

    return jsonify({"status": "success", "message": "Join network","active_peers": active_peers,"peerPort":port}), 200

        
@app.route("/leave", methods=["POST"]) # Déconnexion noeuds
def leave_network():
    print(f"[DEBUG] Request Data: {request.data}")  # Affiche les données de la requête
    
    data = request.get_json()    
    peer_port = int(data.get("peerPort")) if data else None
    print(f"[DEBUG] peer_port = {peer_port} type : {type(peer_port)}")
    
    if peer_port:
        dht_local = load_variable_json(peer_port, "dht")
        responsability_plage = load_variable_json(peer_port, "responsability_plage")
        active_peers = load_variable_json(peer_port, "active_peers")
        print(f"[DEBUG] active_peers = {active_peers}")
        my_node = load_variable_json(peer_port, "my_node")
        bootstrap_interaction("LEAVE", peer_port, active_peers=active_peers)  
    else:
        print("[DEBUG] No peerPort received.")
    
    return jsonify({"status": "success", "message": "Left network"}), 200

@app.route("/info", methods=["POST"]) #Informations réseau
def get_peers():

    data = request.get_json()
    print("[DEBUG] Requête reçue:", data)  # Vérifier ce qui est reçu

    peer_port = int(data.get("peerPort")) if data else None
    print("[DEBUG] peer_port =", peer_port)

   
    if peer_port :
        dht_local = load_variable_json(peer_port, "dht" )
        responsability_plage = load_variable_json(peer_port, "responsability_plage" )
        active_peers = load_variable_json(peer_port, "active_peers" )
        my_node = load_variable_json(peer_port, "my_node" )


        print("Plage de responsabilité :", load_variable_json(peer_port,"responsability_plage"))
        print("Liste des pairs actifs :", active_peers)
        print("dht local :",dht_local)

        result = []
        for peer in active_peers:
            result.append({"my_node": my_node,
                           "active_peers": peer,
                           "dht_local": dht_local})
            

        return jsonify({"Status": "success","data": result}), 200


    else:
        print("[DEBUG] No peerPort received.")

    return jsonify({"Status": "error", "message": "No peerPort provided"}), 400


# @app.route("/dht", methods=["GET"])
# def get_dht():
#     return jsonify({"dht_local": dht_local}), 200

# @app.route("/add_file", methods=["POST"])
# def add_file():
#     data = request.json
#     file_path = data.get("file_path")
#     # Ajouter ton code ici pour gérer l'ajout de fichiers
#     return jsonify({"status": "success", "message": "File added successfully"}), 200

UPLOAD_FOLDER = "uploads"  # Dossier où sauvegarder temporairement les fichiers
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Crée le dossier s'il n'existe pas

def save_file_key(filename,key, output_file="file_keys.txt"):
    with open(output_file, "a", encoding ='utf-8') as f:
        f.write(f"{filename} : {key}\n")
    print(f"[INFO] Enregistrement : {filename} -> {key}")

@app.route("/upload", methods = ["POST"])
def upload_file():

    print("[DEBUG] Requête reçue") 

    if "file" not in request.files:
        print("[DEBUG] Aucun fichier reçu")
        return jsonify({"status": "error", "message": "Aucun fichier fourni"}), 400

    file = request.files["file"]  # On récupère le fichier correctement
    peer_port = request.form.get("peerPort")  # On récupère peerPort

    print(f"[DEBUG] peer_port = {peer_port}, fichier = {file.filename}")

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)  # ⬅️ Correction : on enregistre le fichier

    
    # data = request.get_json()
    # print("[DEBUG] Requête reçue:", data)  # Vérifier ce qui est reçu

    # peer_port = int(data.get("peerPort")) if data else None
    # print("[DEBUG] peer_port =", peer_port)

    dht_local = load_variable_json(peer_port, "dht" )
    responsability_plage = load_variable_json(peer_port, "responsability_plage" )
    active_peers = load_variable_json(peer_port, "active_peers" )
    my_node = load_variable_json(peer_port, "my_node" )
    print(my_node)
    # fichier = "IMG_20170915_173150.jpg"
    fichier_coder,key = create_add_file_message(file_path, my_node)
    print("[DEBUG] Fichier Coder :", fichier_coder)
    print("[DEBUG] KEY", key)

    add_file_to_network(file_path,f'.storage{peer_port}')
    send_replica_message(my_node,active_peers,key)
    data= {"action":"add_file", "data": fichier_coder}
    dht_local=handle_dht(my_node,active_peers,data, dht_local, responsability_plage)
    update_or_add_variable(peer_port, "dht", dht_local)

    #Ecriture dans le fichier file_keys.txt
    save_file_key(file.filename,key=key)


    # if request_pow_verification(active_peers, key, my_node, 2):

    #     print("[DEBUG] PASS request_pow_verify")
    #     add_file_to_network(file,f'.storage{peer_port}')
    #     send_replica_message(my_node,active_peers,key)
    #     data= {"action":"add_file", "data": fichier_coder}
    #     dht_local=handle_dht(my_node,active_peers,data, dht_local, responsability_plage)
    #     update_or_add_variable(peer_port, "dht", dht_local)

    return jsonify({"status": "success", "message": f"Fichier {file.filename} reçu avec peerPort {peer_port}"}), 200

@app.route("/download",methods=["POST"])
def donwload_file():
    print("[DEBUG] requete passée")

    data = request.get_json()
    print("[DEBUG] Requête reçue:", data)  # Vérifier ce qui est reçu
    file_name = data.get("filename")
    peer_port = int(data.get("peerPort")) if data else None
    print("[DEBUG] peer_port =", peer_port,"file name : ", file_name)

    if peer_port is None:
        return jsonify({"status": "error", "message": "peerPort manquant"}), 400

    dht_local = load_variable_json(peer_port, "dht" )
    responsability_plage = load_variable_json(peer_port, "responsability_plage" )
    active_peers = load_variable_json(peer_port, "active_peers" )
    my_node = load_variable_json(peer_port, "my_node" )
    message=create_looking_file_message(file_name,my_node)
    data= {"action":"looking_file", "data": message}
    request_list_peer_have_file(my_node,active_peers,data, dht_local, responsability_plage)
    #request_files([['127.0.0.1',7002],['127.0.0.1',7001]],"d82976927a30836e3d26fbdc83289539dc65229522676d071b3894e8478af059841e402823a16a394fe1c420483932a9b78ce18dcebe2a582c7fcb7f3faf33a2",my_node)


    return jsonify({"status": "success", "message": "Téléchargement initié"}), 200



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)  

