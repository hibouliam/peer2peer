from flask import Flask, jsonify,request
import subprocess
import os
import socket
import random
from flask_cors import CORS
from recup_ip import generate_key
import msgpack
from dht import assign_dht, request_dht,handle_dht, send_dht_local,create_add_file_message, create_looking_file_message, request_list_peer_have_file, send_replica_message,create_delete_file_message
from file_share import request_files,handle_files
from file_emplacement import add_file_to_network
from new_conn_bootstrap import bootstrap_interaction,attempt_peer_connections,start_peer_server,handle_communication_between_peer,add_neighbor_peer,applatir_données
import random, threading

app = Flask(__name__)
CORS(app)
global responsability_plage
active_peers = []
dht_local = {}

@app.route('/api/ip', methods=['GET'])
def get_ip():
    """ Remplissage automatique du champ IP"""
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    # bootstrap_interaction(action="JOIN", active_peers = active_peers) #rejoindre le réseau
    # if active_peers is None:
    #     return jsonify({"error": "Impossible de récupérer la liste des pairs"}), 500
    # return jsonify({"message": "Rejoint avec succès", "active_peers": active_peers,"ip": request.remote_addr})
    return jsonify({"ip": ip_address})

@app.route('/join_network', methods=['POST'])
def start_peer():
    """ Se connecter au réseau P2p"""
    global active_peers, responsability_plage
    port  = random.randint(1024, 65535)
    my_node = [generate_key(f'127.0.0.1:{port}'),'127.0.0.1',port]
    
    result = bootstrap_interaction("JOIN", active_peers, port)
    if result:
        active_peers = result[0]  # Récupère la liste des pairs actifs si elle est retournée
        print(f"Active Peers après JOIN : {active_peers}")  # Debug(active_peers)
        
        server_thread = threading.Thread(target=start_peer_server, args=(port, my_node))
        server_thread.daemon = True
        server_thread.start()

        # Se connecter aux autres pairs du réseau
        attempt_peer_connections(my_node)
        responsability_plage=assign_dht(my_node, active_peers)
        print(f"[start_peer] Plage de responsabilité assignée : {responsability_plage}")  # Debug

        if responsability_plage is None:
            print("[start_peer] Erreur: la plage de responsabilité n'a pas pu être définie")
            return jsonify({"error": "Erreur lors de l'assignation de la DHT"}), 500

        request_dht(my_node, active_peers, responsability_plage)
        
         # Écriture des informations dans un fichier
        file_path = "network_nodes.txt"
        with open(file_path, "a") as file:  
            file.write(f"Port: {port}, Node: {my_node}, Plage: {responsability_plage}\n")

        return jsonify({"message": "Peer started", "port": port,"responsability_plage": responsability_plage}), 200
    
    return jsonify({"error": "Impossible de rejoindre le réseau"}), 500

@app.route('/leave_network',methods=['POST'])
def stop_peer(port):
    """ Quitter le réseau """
    bootstrap_interaction("LEAVE", active_peers,)  # Tester l'action LEAVE


@app.route('/info', methods=['GET'])
def print_info():
    """ Infos sur les pairs en cours d'exécution """
    # global responsability_plage
    # print("Plage de responsabilité :", responsability_plage)
    print("Liste des pairs actifs :", active_peers)
    print("dht local :",dht_local)
     # Retourner les informations sous forme de JSON
    return jsonify({
        "active_peers": active_peers,
        "dht_local": dht_local
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
