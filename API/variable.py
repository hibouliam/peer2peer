import json
import os

def create_variable_json(PEER_PORT):
    storage_dir = f'.storage{PEER_PORT}'
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)
    
    file_path = os.path.join(storage_dir, "variable.json")
    
    if not os.path.isfile(file_path):
        default_data = {
            "port": PEER_PORT,
            "dht": {},
            "responsability_plage": (0, None)
        }
        
        with open(file_path, 'w') as json_file:
            json.dump(default_data, json_file, indent=4)
        
        print(f"Fichier {file_path} créé avec succès.")
    else:
        print(f"Le fichier {file_path} existe déjà.")

def load_variable_json(PEER_PORT, variable):
    """
    Charge un fichier JSON et retourne la valeur de la variable spécifiée.
    Si la variable est 'responsability_plage', elle est transformée en tuple.
    
    """
    storage_dir = f'.storage{PEER_PORT}'
    file_path = os.path.join(storage_dir, "variable.json")
    
    if os.path.isfile(file_path):
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)

        if variable in data:
            result = data[variable]
            
            if variable == "responsability_plage" and isinstance(result, list) and len(result) == 2:
                result = (result[0], None if result[1] is None else result[1])
                print(f"Variable '{variable}' transformée en tuple : {result}")
            
            print(f"Variable '{variable}' chargée avec succès.")
            return result
        else:
            print(f"La variable '{variable}' n'existe pas dans le fichier.")
            return None
    else:
        print(f"Le fichier {file_path} n'existe pas.")
        return None


def update_or_add_variable(PEER_PORT, variable_name, new_value):
    storage_dir = f'.storage{PEER_PORT}'
    file_path = os.path.join(storage_dir, "variable.json")
    
    if os.path.isfile(file_path):
        # Charger les données existantes
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
        
        # Mettre à jour ou ajouter la variable
        data[variable_name] = new_value
        
        # Réécrire les données mises à jour dans le fichier
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        
        print(f"Variable '{variable_name}' mise à jour/ajoutée avec succès.")
    else:
        print(f"Le fichier {file_path} n'existe pas.")