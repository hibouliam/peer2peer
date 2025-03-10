from flask import Flask, request
from t import PeerNode
app = Flask(__name__)

# Démarrer plusieurs instances de PeerNode avec des ports différents
peer_nodes = {
    5004: PeerNode(5004),
    5002: PeerNode(5002),
    5003: PeerNode(5003)
}

peer_nodes = {}

@app.route("/join_network", methods=["POST"])
def join_network():
    # Récupérer le port depuis le corps de la requête JSON
    data = request.get_json()
    port = data.get("port")

    if port:
        if port not in peer_nodes:
            peer_nodes[port] = PeerNode(port)
        
        active_peers = peer_nodes[port].bootstrap_interaction("JOIN")
        return {"message": "Joined network", "active_peers": active_peers}, 200
    else:
        return {"error": "Port is required"}, 400

@app.route("/leave_network", methods=["POST"])
def leave_network():
    # Récupérer le port depuis le corps de la requête JSON
    data = request.get_json()
    port = data.get("port")

    if port in peer_nodes:
        peer_nodes[port].bootstrap_interaction("LEAVE")
        del peer_nodes[port]  # Supprimer l'instance du peer
        return {"message": "Left network"}, 200
    else:
        return {"error": "Invalid port"}, 400


@app.route("/add_file", methods=["POST"])
def add_file():
    # Récupérer le port et le fichier depuis la requête JSON
    data = request.get_json()
    port = data.get("port")
    file = data.get("file")

    if port in peer_nodes and file:
        peer_nodes[port].add_file_to_network(file, f'.storage{port}')
        return {"message": "File added"}, 200
    else:
        return {"error": "Invalid port or file missing"}, 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)