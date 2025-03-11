from flask import Flask, request,jsonify
from flask_cors import CORS
import threading,sys,random,socket
from recup_ip import generate_key
import msgpack
from dht import assign_dht, request_dht,handle_dht, send_dht_local,create_add_file_message, create_looking_file_message, request_list_peer_have_file, send_replica_message,create_delete_file_message
from file_share import request_files,handle_files
from file_emplacement import add_file_to_network
# from sans_global import bootstrap_interaction,attempt_peer_connections,start_peer_server,handle_communication_between_peer,add_neighbor_peer,applatir_données
from variable import create_variable_json, update_or_add_variable, load_variable_json
from conn_bootstrap import bootstrap_interaction,attempt_peer_connections,start_peer_server,handle_communication_between_peer,add_neighbor_peer,applatir_données
   

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

active_peers = []
dht_local = {}
lock = threading.Lock()

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
    server_thread = threading.Thread(target=start_peer_server(port)) # Création d'un thread pour gérer la connexion entre 2 pairs avec la fonction start_peer_server
    server_thread.daemon = True
    server_thread.start()

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

    return jsonify({"status": "success", "message": "Join network","active_peers": active_peers}), 200

        
@app.route("/leave", methods=["POST"])
def leave_network():
    data = request.json
    peer_port = data.get("peer_port")
    bootstrap_interaction("LEAVE", active_peers, peer_port)
    return jsonify({"status": "success", "message": "Left network"}), 200

@app.route("/peers", methods=["GET"])
def get_peers():
    return jsonify({"active_peers": active_peers}), 200

# @app.route("/dht", methods=["GET"])
# def get_dht():
#     return jsonify({"dht_local": dht_local}), 200

# @app.route("/add_file", methods=["POST"])
# def add_file():
#     data = request.json
#     file_path = data.get("file_path")
#     # Ajouter ton code ici pour gérer l'ajout de fichiers
#     return jsonify({"status": "success", "message": "File added successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)  

