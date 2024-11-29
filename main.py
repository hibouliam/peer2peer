import socket
import threading
import json
import sys
from recup_ip import generate_key
import msgpack


from conn_bootstrap import bootstrap_interaction,attempt_peer_connections,start_peer_server

BOOTSTRAP_HOST = '127.0.0.1'  # Adresse du serveur bootstrap
BOOTSTRAP_PORT = 5001     # Port du bootstrap
PEER_PORT = 7002         # Port d'écoute du pair

active_peers = []  # Liste des pairs actifs

peer=[]


try:
    while True:
        print("\nActions disponibles :")
        print("1. Tapez 'j' pour rejoindre le réseau.")
        print("2. Tapez 'q' pour quitter le réseau.")
        
        action = input("Votre choix : ").lower()

        if action == 'j':
            bootstrap_interaction("JOIN")  # Tester l'action JOIN
            server_thread = threading.Thread(target=start_peer_server) # Création d'un thread pour gérer la connexion entre 2 pairs avec la fonction start_peer_server
            server_thread.daemon = True
            server_thread.start()
            # Se connecter aux autres pairs du réseau
            attempt_peer_connections()
            #Reste à faire
            print("Liste des pairs actifs :", active_peers)

            #Tester voir si ca fonctionne
            #Si ca fonctionne faut faire une fonction pour dire qu'il est responsable de la plage de lui à son voisin suivant
            #Faire deux exceptions : - si ces deux voisins sont plus grands alors il est reponsable de 0 au voisin le plus proche de lui (par exemple si 1 a comme voisin 2 et 5 alors il responsable de 0 à 2 )
                                   # - si ces deux voisins sont plus petits alors il est reponsable  de lui à +infini (par exemple si 5 a comme voisin 1 et 4 alors il est responable de 5 à +infini)
            #Et pour l'écriture de la dht je propose soit dictionnaire map (dht={"file1":["12 7.0.0.1:8000","127.0.0.1:5000"]})  
            #Ou alors directement dans un fichier json  / on peut regarder messagepack(facile) ou protocol buffer (dfficle mais plus sécurisé)
            #Perso je pense que peu importe lequel on utilise on pourra changer facilement pcq ca reste un peu la même chose

            #Ca c'est autre chose
            #Enregistrer l'adresse ip de deux paires (celui a qui il envoie et celui qui recoit le message)
            #Gerer les déconnexions en envoyant le peer suivant au noeud précédent 
            #Peut être faire un test toute les x secondes pour verifier la connexion
        elif action == 'q':
            bootstrap_interaction("LEAVE")  # Tester l'action LEAVE
            break  # Sortie de la boucle après avoir quitté le réseau
        else:
            print("Choix non valide. Veuillez taper 'j' ou 'q'.")
            
except KeyboardInterrupt:
    print("\nInterruption par l'utilisateur. Déconnexion en cours...")
    bootstrap_interaction("LEAVE")
