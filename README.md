# peer2peer
Création d'un réseau peer2peer

Objectif fixé par le prof :
Ce projet vise à développer un petit réseau peer-to-peer pour le partage d'images, de documents et d'autres fichiers. L’objectif est de permettre aux utilisateurs de partager des fichiers directement entre eux de manière sécurisée.

Livrable
L’application livrée devra comporter les fonctionnalités suivantes :
- Rejoindre / quitter le réseau (les fichiers seront redistribuées)
- Ajouter un fichier
- Télécharger un fichier

Options a ajouter pour un projet complet :
- Permettre d'envoyer/demander un fichier à une personne cible
- faire une interface par flutter PC/IOS/android
- Chercher a publier et herberger le site eventuellement (au moins le site web)

## Les grandes étapes
### 1-identifier des pairs sur le réseau 
### 2-Etablir une connexion P2P entre les pairs
### 3-Redistribuer les fichiers si un utilisateur quitte le réseau
### 4-Ajout d'un fichier
### 5-Téléchargement d'un fichier
### 6-Sécuriser le tout
### 7-Faire une interface user

Résumé des appels principaux dans l'ordre
Pour un cycle complet du partage de fichier entre pairs :

Initialisation et enregistrement :

Peer.__init__()
register_peer() → (appelant) get_file_list(), self.service.put()
Démarrage des threads de serveur et gestion des fichiers :

peer_server() via PeerOperations("PeerServer", p)
peer_file_handler() via PeerOperations("PeerFileHandler", p)
Requête de recherche et obtention de fichier :

search_file()
obtain()
Réception de requêtes entrantes et transfert de fichier :

peer_server_listener()
peer_server_upload()
Réplication pour la redondance :

data_resilience()
