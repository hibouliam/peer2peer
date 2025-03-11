import socket
import msgpack # type: ignore
import time
import os
import glob

def get_free_port():
    """Trouve un port libre sur le système."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))  # Laisser choisir un port libre
        return s.getsockname()[1]  # Retourner le port sélectionné

def request_files(list_peer_have_files: list, looking_key: str, my_node: list, save_directory=".."):
    """
    Demande un fichier aux pairs disponibles jusqu'à réception réussie.
    Utilise un port différent à chaque tentative pour plus de sécurité.
    """
    try :
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as response_socket:
            response_socket.connect((list_peer_have_files[0][1], 5005))  # Connexion à l'IP de l'expéditeur
            response_socket.sendall(b"REQUEST")  # Envoi de l'accusé de réception
            print(f"Accusé de réception envoyé à {list_peer_have_files[0][1]} sur le port {5005}")    
    except :
        print("no")
    message = {
        "action": "request_file",
        "key": looking_key,
        "applicant": my_node
    }

    for peer in list_peer_have_files:
        if peer != my_node :
            peer_ip, peer_port = peer[1], peer[2]
            my_free_port = get_free_port()  

            print(f"Tentative de récupération du fichier auprès de {peer_ip}:{peer_port} sur le port {my_free_port}")

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)  
                    s.connect((peer_ip, peer_port)) 
                    message["port"] = my_free_port 
                    s.sendall(msgpack.packb(message))
                    print(f"Message envoyé à {peer_ip}:{peer_port}")

                if receive_file(port=my_free_port, save_directory=save_directory, AUTHORIZED_IP=peer_ip):
                    print("Fichier reçu avec succès.")
                    return True 
            
            except Exception as e:
                print(f"Échec avec {peer_ip}:{peer_port} - {e}")

        time.sleep(1)  # Délai aléatoire pour éviter les schémas prévisibles

    print("Échec de récupération du fichier : aucun pair ne l'a fourni.")
    return False


    
def send_file(filename, host, port):
    """Envoie un fichier à un pair via sockets."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        filesize = os.path.getsize(filename)
        s.sendall(f"{os.path.basename(filename)}|{filesize}".encode())
        ack = s.recv(1024).decode()
        if ack != "READY":
            print("Erreur lors de l'envoi.")
            return
        
        with open(filename, "rb") as f:
            while (chunk := f.read(1024)):
                s.sendall(chunk)

        confirmation = s.recv(1024).decode()
        if confirmation == "RECEIVED":
            print("Accusé de réception reçu. L'envoi est terminé.")        

        print("Fichier envoyé avec succès.")

def receive_file(port, save_directory=".",AUTHORIZED_IP=""):
    """Reçoit un fichier UNIQUEMENT de l'IP autorisée et le stocke dans le dossier spécifié."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", port))
        s.listen(1)
        print(f"En attente d'une connexion sur le port {port}...")

        while True:
            conn, addr = s.accept()
            
            # Vérifier si l'IP est autorisée
            if addr[0] != AUTHORIZED_IP:
                print(f"Connexion refusée de {addr[0]}")
                conn.close()
                continue  # Attendre une autre connexion

            print(f"Connexion acceptée de {addr[0]}")

            with conn:
                metadata = conn.recv(1024).decode()
                filename, filesize = metadata.split("|")
                filename = os.path.join(save_directory, filename)
                filesize = int(filesize)
                conn.sendall(b"READY")
                received_size = 0
                with open(filename, "wb") as f:
                    while received_size < filesize:
                        chunk = conn.recv(1024)
                        if not chunk:
                            break
                        f.write(chunk)
                        received_size += len(chunk)
                conn.sendall(b"RECEIVED")
                print("HELLO")
                try :
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as response_socket:
                        response_socket.connect((addr[0], 5005))  # Connexion à l'IP de l'expéditeur
                        response_socket.sendall(b"RECEIVED")  # Envoi de l'accusé de réception
                        print(f"Accusé de réception envoyé à {addr[0]} sur le port {5005}")
                    print("hello")
                    return True  # Indiquer que le fichier a été reçu avec succès
                except :
                    print("test")
                    return True


def handle_files(received_data:dict, Storage):
    """
    Gère les communications pour les échanges de fichiers
    """
    try:
        looking_key = received_data.get("key")
        applicant = received_data.get("applicant")
        host = applicant[1]
        port = received_data.get("port")

        file_pattern = os.path.join(Storage, f"{looking_key}.*")
        matching_files = glob.glob(file_pattern)

        if matching_files:
            file_path = matching_files[0]  # Prend le premier fichier trouvé
            send_file(file_path, host, port)
            print(f"Fichier {file_path} envoyé à {host}:{port}")
        else:
            print(f"Aucun fichier correspondant à {looking_key}")
    
    except Exception as e:
        print(f"Problème avec handle_files : {e}")

import socket

def wait_for_connection(timeout=None):
    

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", 5005)) 
    s.listen(1)
    print("En attente de connexions sur le port 12345...")
    if timeout:
        s.settimeout(timeout)
    while True:
        conn, addr = s.accept()
        print(f"Connexion acceptée de {addr}")

        # Traite les données envoyées par le client
        data = conn.recv(1024)
        print(f"Données reçues : {data.decode()}")
        if data.decode() == "REQUEST":
            print("Accusé de réception reçu.")
            conn.close()  # Fermer la connexion
            return False
        if data.decode() == "RECEIVED":
            print("Accusé de réception reçu.")
            conn.close()  # Fermer la connexion
            return True
 
