active_peers =[['5fe96ad748b11f2e00af23d0899e1bcff4655811831499732e5193937e3c8072fc9f44060acb7db8a3969c0a3df7fc5f52f0607d137bd684725081e6c3894f19', '127.0.0.1', 7001], ['b048dee8bf0ca95792006780bf7cff3a68cb4e37ff35b36313bd83576b02021ce7c0410b8a35613f6ae26507e788f7d4d6af389ec716a9c95729b486e063b20e', '127.0.0.1', 7004]]
peer = ['6fe96ad748b11f2e00af23d0899e1bcff4655811831499732e5193937e3c8072fc9f44060acb7db8a3969c0a3df7fc5f52f0607d137bd684725081e6c3894f19', '127.0.0.1', 7002]
def assign_dht(peer: list,active_peers:list) -> tuple :
    """
    Asssigne la plage de la dht au pair en fonction de ses voisins
    """
    peer_key = int(peer [0],16)
    
    left_neighbor_key = int(active_peers [0][0],16)
    right_neighbor_key = int(active_peers [1][0],16)
    return determine_responsibility (peer_key,left_neighbor_key,right_neighbor_key)

def determine_responsibility(peer_key : int, left_neighbor_key : int, right_neighbor_key :int) -> tuple:
    """
    Détermine la plage de responsabilité pour un pair dans une DHT allant de 0 à +infini.
    - si ses deux voisins sont plus grands alors il est reponsable de 0 au voisin le plus proche de lui (par exemple si 1 a comme voisin 2 et 5 alors il responsable de 0 à 2 )
    - si ses deux voisins sont plus petits alors il est reponsable  de lui à +infini (par exemple si 5 a comme voisin 1 et 4 alors il est responable de 5 à +infini)
    - sinon il est responsable de lui à son voisin le plus grand
    """

    if left_neighbor_key> peer_key and right_neighbor_key> peer_key :
        return (0, min(left_neighbor_key,right_neighbor_key))
    if left_neighbor_key< peer_key and right_neighbor_key<peer_key :
        return (peer_key, None)
    else :
        return(peer_key, max(left_neighbor_key,right_neighbor_key))
    
print(assign_dht(peer, active_peers))
    