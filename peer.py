import hashlib

def generate_key(filename):
    """Génère une clé unique pour un fichier en utilisant SHA-224."""
    return hashlib.sha3_512(filename.encode()).hexdigest()

print(generate_key("test.txt"))

import socket
import threading

class DHTNode:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.id = generate_key(f"{host}:{port}")  # ID du nœud basé sur son adresse
        self.files = {}  # Stocke les fichiers et leur contenu
        self.routing_table = {}  # Table de routage vers d'autres nœuds
        
        # Démarrer le serveur pour écouter les requêtes
        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.start()

    def add_file(self, filename, content):
        """Ajoute un fichier au nœud et le partage dans le réseau."""
        file_key = generate_key(filename)
        self.files[file_key] = content
        print(f"Fichier ajouté localement : {filename} (clé: {file_key})")

    def start_server(self):
        """Démarre un serveur pour écouter les requêtes de recherche de fichiers."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen()
        print(f"Nœud {self.id} en écoute sur {self.host}:{self.port}")
        
        while True:
            client_socket, _ = server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        """Gère les requêtes reçues des autres nœuds."""
        request = client_socket.recv(1024).decode()
        command, key = request.split()
        
        if command == "SEARCH":
            if key in self.files:
                client_socket.send(f"FOUND {self.host}:{self.port}".encode())
            else:
                client_socket.send("NOT_FOUND".encode())
        client_socket.close()

    def search_file(self, file_key):
        """Recherche un fichier dans le réseau."""
        # Pour simplifier, ici on cherche uniquement dans le nœud actuel.
        # En réalité, il faudrait parcourir la DHT via la table de routage.
        if file_key in self.files:
            print(f"Fichier trouvé localement : clé {file_key}")
            return self.host, self.port
        else:
            for node_id, address in self.routing_table.items():
                if self.contact_node(address, file_key):
                    return address
        return None

    def contact_node(self, address, file_key):
        """Contacte un autre nœud pour voir s'il possède le fichier."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(address)
            sock.send(f"SEARCH {file_key}".encode())
            response = sock.recv(1024).decode()
            return response.startswith("FOUND")


# Exemple d'utilisation du nœud
node1 = DHTNode("127.0.0.1", 5001)
node2 = DHTNode("127.0.0.1", 5002)

# Ajouter des fichiers au nœud 1
node1.add_file("document1.txt", "Ceci est le contenu du document 1.")
node1.add_file("document2.txt", "Ceci est le contenu du document 2.")

# Ajout du nœud 2 dans la table de routage de node1
node1.routing_table[node2.id] = ("127.0.0.1", 5002)

# Rechercher un fichier via sa clé
file_key = generate_key("document1.txt")
address = node1.search_file(file_key)
if address:
    print(f"Fichier trouvé à l'adresse : {address}")
else:
    print("Fichier non trouvé.")
