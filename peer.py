import hashlib
import sys

def generate_key(filename):
    """Génère une clé unique pour un fichier en utilisant SHA-224 : Principe de hachage"""
    return hashlib.sha3_512(filename.encode()).hexdigest()

#print(generate_key("test.txt"))

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

    def display_routing_table(self):
        """Affiche le contenu de la table de routage"""
        if not self.routing_table:
            print("La table de routage est vide.")
        else:
            print(f"Table de routage pour le nœud {self.id} ({self.host}:{self.port}):")
            for node_id, address in self.routing_table.items():
                print(f"- ID: {node_id}, Adresse: {address}")

    def add_file(self, filename, content):
        """Ajoute un fichier au nœud et le partage dans le réseau."""
        file_key = generate_key(filename)
        self.files[file_key] = content
        print(f"Fichier ajouté localement : {filename} (clé: {file_key})")


    def download_file(self, file_key):
        """Télécharge un fichier du réseau."""
        # Rechercher dans le réseau quel nœud détient le fichier.
        print(f"Recherche du fichier avec la clé {file_key} dans le réseau...")
        
        address = self.search_file(file_key)  # Recherche du fichier dans le réseau via la DHT
        
        if address is None:
            print(f"Fichier {file_key} non trouvé dans le réseau.")
            return None

        # Une fois qu'un nœud est trouvé, on télécharge le fichier depuis ce nœud
        print(f"Fichier {file_key} trouvé à l'adresse {address}. Tentative de téléchargement...")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(address)
                sock.send(f"DOWNLOAD {file_key}".encode())  # Envoie une requête pour télécharger le fichier
                
                # Attente de la réponse du nœud distant
                response = sock.recv(4096).decode()

                if response.startswith("FILE_CONTENT"):
                    content = response.split(" ", 1)[1]  # Le contenu du fichier est après "FILE_CONTENT"
                    print(f"Contenu du fichier téléchargé : {content}")
                    return content
                else:
                    print("Fichier non trouvé sur le nœud distant.")
                    return None

        except Exception as e:
            print(f"Erreur lors du téléchargement du fichier : {e}")
            return None


    def send_file(self, address, file_key):
        """Envoie un fichier à un nœud distant lorsqu'il en fait la demande."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(address)
                # Envoie du fichier sous forme de réponse
                if file_key in self.files:
                    content = self.files[file_key]
                    sock.send(f"FILE_CONTENT {content}".encode())
                    print(f"Fichier {file_key} envoyé à {address}")
                else:
                    sock.send("FILE_NOT_FOUND".encode())
                    print(f"Le fichier {file_key} n'a pas été trouvé localement.")
        
        except Exception as e:
            print(f"Erreur lors de l'envoi du fichier à {address} : {e}")

    
    def request_file(self, target_node_address, file_key):
        """Demande un fichier à un nœud cible en envoyant la commande DOWNLOAD."""
        try:
            # Connexion au nœud cible
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(target_node_address)  # Connexion au nœud cible

                # Envoi de la commande DOWNLOAD avec la clé du fichier
                sock.send(f"DOWNLOAD {file_key}".encode())

                # Réception de la réponse du nœud cible
                response = sock.recv(4096).decode()

                # Vérification de la réponse
                if response.startswith("FILE_CONTENT"):
                    # Le fichier a été trouvé et son contenu est renvoyé
                    content = response.split(" ", 1)[1]
                    print(f"Contenu du fichier téléchargé depuis le nœud cible : {content}")
                    return content
                elif response == "FILE_NOT_FOUND":
                    print("Le fichier demandé n'a pas été trouvé sur le nœud cible.")
                    return None
                else:
                    print("Réponse inattendue du nœud cible.")
                    return None

        except Exception as e:
            print(f"Erreur lors de la demande du fichier au nœud cible {target_node_address}: {e}")
            return None


    def start_server(self):
        """Démarre un serveur pour écouter les connexions entrantes et lance un nouveau thread pour chaque client."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # socket TCP (SOCK_STREAM) en utilisant IPv4 (AF_INET)
        server_socket.bind((self.host, self.port))
        server_socket.listen()
        print(f"Nœud {self.id} en écoute sur {self.host}:{self.port}")

        while True:
            client_socket, _ = server_socket.accept() # Acceptation des connexions entrantes
            threading.Thread(target=self.handle_client, args=(client_socket,)).start() # Création d'un thread pour gérer le client

    # def leave_network(self):
    #     """
    #     Quitter proprement le réseau DHT en informant les autres nœuds dans la table de routage.
    #     """
    #     print(f"Nœud {self.id} se déconnecte du réseau...")
    #     for node_id, address in self.routing_table.items():
    #         try:
    #             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    #                 sock.connect(address)
    #                 message = f"LEAVE {self.id}"
    #                 sock.send(message.encode())
    #         except Exception as e:
    #             print(f"Erreur lors de la notification de déconnexion au nœud {address}: {e}")
        
    #     print("Tous les nœuds ont été informés de la déconnexion.")
    #     sys.exit()

    def handle_client(self, client_socket):
        """Gère les requêtes reçues/entrantes des autres nœuds."""
        try:
            request = client_socket.recv(1024).decode()  # Reception de la requête entrante + Décodage
            if not request:
                return

            # Commande et clé du fichier sont séparés par un espace
            command, key = request.split()

            # Gestion de la commande SEARCH
            if command == "SEARCH":
                if key in self.files:
                    # Si le fichier est local, renvoyer l'adresse du nœud courant
                    client_socket.send(f"FOUND {self.host}:{self.port}".encode())
                else:
                    # Si le fichier n'est pas local, renvoyer "NOT_FOUND"
                    client_socket.send("NOT_FOUND".encode())

            # Gestion de la commande DOWNLOAD
            elif command == "DOWNLOAD":
                # Si le fichier est trouvé localement
                if key in self.files:
                    content = self.files[key]  # Récupération du contenu du fichier
                    client_socket.send(f"FILE_CONTENT {content}".encode())  # Envoi du contenu du fichier
                else:
                    # Si le fichier n'est pas trouvé localement
                    client_socket.send("FILE_NOT_FOUND".encode())

            # Gestion de la commande SEND_FILE
            elif command == "SEND_FILE":
                # Si un nœud demande un fichier, on envoie le fichier s'il existe
                if key in self.files:
                    # Si le fichier existe localement, on envoie son contenu
                    content = self.files[key]
                    self.send_file(client_socket, content)  # Appel à la méthode pour envoyer le fichier
                else:
                    # Si le fichier n'est pas trouvé localement
                    client_socket.send("FILE_NOT_FOUND".encode())

        except Exception as e:
            print(f"Erreur lors de la gestion du client : {e}")
        finally:
            client_socket.close()



    # def search_file(self, file_key):
    #     """Recherche un fichier localement,  et si introuvable, envoie une requête de recherche aux autres nœuds du 
    #     réseau via la table de routage"""
    #     # Pour simplifier, ici on cherche uniquement dans le nœud actuel.
    #     # En réalité, il faudrait parcourir la DHT via la table de routage.
    #     if file_key in self.files:
    #         print(f"Fichier trouvé localement : clé {file_key}")
    #         return self.host, self.port
    #     else:
    #         for node_id, address in self.routing_table.items():
    #             if self.contact_node(address, file_key):
    #                 return address
    #     return None
    
    def search_file(self, file_key):
        """Recherche un fichier dans le réseau via une recherche étendue dans la DHT."""

        if file_key in self.files:
            print(f"Fichier trouvé localement : clé {file_key}")
            return self.host, self.port
        
        visited_nodes = set()  # Pour éviter les recherches en boucle
        nodes_to_visit = list(self.routing_table.values())

        while nodes_to_visit:
            address = nodes_to_visit.pop(0)
            if address not in visited_nodes:
                visited_nodes.add(address)
                if self.contact_node(address, file_key):
                    return address
        
        print("Fichier non trouvé dans le réseau.")
        return None


    def contact_node(self, address, file_key):
        try : 
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock: # Création d'une connexion socket
                sock.connect(address) # Connexion au nœud cible
                sock.send(f"SEARCH {file_key}".encode()) # commande de recherche "SEARCH" suivie de la clé du fichier (file_key) au nœud cible
                response = sock.recv(1024).decode() # Réception de la réponse
                return response.startswith("FOUND")
        except Exception as e:
            print(f"Erreur lors de la connexion au nœud {address}: {e}")
            return False


###### Exemple d'utilisation recherche de fichier
# # Exemple d'utilisation du nœud
# node1 = DHTNode("127.0.0.1", 5001)
# node2 = DHTNode("127.0.0.1", 5002)
# node3 = DHTNode("127.0.0.1", 5003)
# node4 = DHTNode("127.0.0.1", 5004)
# node5 = DHTNode("127.0.0.1", 5005)

# # Ajouter des fichiers au nœud 1
# node1.add_file("document1.txt", "Ceci est le contenu du document 1.")
# node2.add_file("document2.txt", "Ceci est le contenu du document 2.")
# node3.add_file("document3.txt", "Ceci est le contenu du document 3.")
# node4.add_file("document4.txt", "Ceci est le contenu du document 4.")
# node5.add_file("document5.txt", "Ceci est le contenu du document 5.")


# # Ajout des noeuf dans la table de routage de node1
# node1.routing_table[node2.id] = ("127.0.0.1", 5002)
# node1.routing_table[node3.id] = ("127.0.0.1", 5003)
# node1.routing_table[node4.id] = ("127.0.0.1", 5004)
# node1.routing_table[node5.id] = ("127.0.0.1", 5005)



# # Recherche de fichiers par `node1` dans le réseau
# fichiers_a_rechercher = ["document1.txt", "document2.txt", "document3.txt", "document4.txt", "document5.txt", "files6.txt"]

# for filename in fichiers_a_rechercher:
#     file_key = generate_key(filename)
#     print(f"\nRecherche du fichier '{filename}' (clé: {file_key}) depuis le nœud 1...")
    
#     # Utiliser la fonction `search_file` pour rechercher dans le réseau
#     address = node1.search_file(file_key)
#     if address:
#         print(f"Fichier '{filename}' trouvé à l'adresse : {address}")
#     else:
#         print(f"Fichier '{filename}' non trouvé dans le réseau.")


###### Exemple d'utilisation du nœud avec option de quitter le réseau
# try:
#     while True:
#         action = input("Tapez 'q' pour quitter le réseau DHT : ")
#         if action.lower() == 'q':
#             node1.leave_network()  # Quitter à partir de `node1`
#             break
# except KeyboardInterrupt:
#     print("\nInterruption par l'utilisateur. Déconnexion en cours...")
#     node1.leave_network()


###### Exemple d'utilisation pour le téléchargement 

node1 = DHTNode("127.0.0.1", 5001)
node2 = DHTNode("127.0.0.1", 5002)

# Ajouter des fichiers au nœud
node1.add_file("document1.txt", "Ceci est le contenu du document 1.")
node2.add_file("document2.txt", "Ceci est le contenu du document 2.")

# Ajouter `node2` dans la table de routage de `node1`
node1.routing_table[node2.id] = ("127.0.0.1", 5002)

# # Recherche et téléchargement d'un fichier
filename = "document2.txt"
file_key = generate_key(filename)
# address = node1.search_file(file_key)

# if address:
#     print(f"Fichier '{filename}' trouvé à l'adresse : {address}")
#     content = node1.download_file(address, file_key)
#     if content:
#         print(f"Contenu du fichier téléchargé : {content}")
# else:
#     print(f"Fichier '{filename}' non trouvé dans le réseau")


#### Exemple d'utilisation pour search_file
# Si le fichier existe dans le nœud 2, on envoie ce fichier à `node2` depuis `node1`
# if file_key in node1.files:
#     print(f"\nEnvoi du fichier 'document2.txt' du nœud 1 vers le nœud 2...")
#     node1.send_file(("127.0.0.1", 5002), file_key)  # Nœud 1 envoie le fichier à nœud 2
# else:
#     print(f"Le fichier 'document2.txt' n'est pas disponible dans le nœud 1.")


#### Exemple d'utilisation pour request_file
# Node1 demande à Node2 de télécharger le fichier
# print(f"Demande de téléchargement du fichier '{filename}' depuis node2 vers node1...")

# # Utiliser l'identifiant pour rechercher dans la table de routage de node1
# target_address = node1.routing_table.get(node2.id)  # Recherche avec l'ID du nœud
# if target_address:
#     content = node1.request_file(target_address, file_key)
#     if content:
#         print(f"Contenu du fichier téléchargé : {content}")
#     else:
#         print("Le fichier n'a pas pu être téléchargé.")
# else:
#     print("Le nœud cible n'a pas été trouvé dans la table de routage.")

# Afficher la table de routage de node1
node1.display_routing_table()