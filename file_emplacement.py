import os
import shutil
from recup_ip import generate_key


def add_file_to_network(file_path, STORAGE_DIR):
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR) 

    with open(file_path, "rb") as f:
        file_content = f.read()

    file_hash = generate_key(str(file_content))
    _, file_extension = os.path.splitext(file_path)
    stored_filename = f"{file_hash}{file_extension}"
    stored_path = os.path.join(STORAGE_DIR, stored_filename)

    if not os.path.exists(stored_path):  
        shutil.copy(file_path, stored_path)
        print(f"Fichier ajouté sous {stored_path}")
    else:
        print("Fichier déjà présent sur le réseau.")

    return stored_filename  

