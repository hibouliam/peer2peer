import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';  // Import du package file_picker

class UploadDialog extends StatefulWidget {
  final VoidCallback onClose;

  UploadDialog({required this.onClose});

  @override
  _UploadDialogState createState() => _UploadDialogState();
}

class _UploadDialogState extends State<UploadDialog> {
  // Créer un TextEditingController pour la barre de recherche
  TextEditingController _searchController = TextEditingController();

  // Fonction pour ouvrir le sélecteur de fichiers
  Future<void> _pickFile() async {
    // Ouvrir le dialogue pour sélectionner un fichier
    FilePickerResult? result = await FilePicker.platform.pickFiles();

    if (result != null) {
      // Si l'utilisateur a sélectionné un fichier
      String? filePath = result.files.single.path;  // Obtenir le chemin du fichier sélectionné
      String fileName = result.files.single.name;  // Obtenir le nom du fichier

      // Afficher le nom du fichier dans la barre de recherche
      _searchController.text = fileName;

      print("File selected: $filePath");
    } else {
      // Si l'utilisateur annule la sélection
      print("No file selected");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 200,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.blueGrey[900],  // Fond sombre bleu-gris pour le thème dark
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(20),  // Arrondir seulement les coins supérieurs
          topRight: Radius.circular(20),
        ),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            'Select the document to upload',
            style: TextStyle(color: Colors.white, fontSize: 18),
          ),
          SizedBox(height: 20),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 30),
            child: Row(
              children: [
                // Champ de texte avec une bordure blanche arrondie
                Expanded(
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.blueGrey[600],  // Couleur de fond
                      borderRadius: BorderRadius.circular(30),  // Bords arrondis
                      border: Border.all(color: Colors.white),  // Bordure blanche
                    ),
                    child: TextField(
                      controller: _searchController,  // Utiliser le controller
                      decoration: InputDecoration(
                        hintText: 'Search your document',
                        hintStyle: TextStyle(color: Colors.white54),  // Texte transparent
                        border: InputBorder.none,  // Pas de bordure
                        contentPadding: EdgeInsets.symmetric(horizontal: 20),
                      ),
                      style: TextStyle(color: Colors.white),
                    ),
                  ),
                ),
                SizedBox(width: 10),  // Espacement entre la barre de recherche et l'icône
                // Icône de dossier à côté de la barre de recherche avec contours (Outlined)
                Container(
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: Colors.white, // Couleur du contour
                      width: 2,  // Épaisseur du contour
                    ),
                    borderRadius: BorderRadius.circular(20),  // Arrondi du contour
                  ),
                  child: IconButton(
                    icon: Icon(
                      Icons.folder_outlined,  // Icône de dossier avec contours
                      color: Colors.white,
                      size: 30,  // Taille de l'icône
                    ),
                    onPressed: _pickFile,  // Lancer la fonction pour ouvrir le sélecteur de fichiers
                  ),
                ),
              ],
            ),
          ),
          SizedBox(height: 20),
          ElevatedButton(
            onPressed: () {
              print("Upload initiated");
              widget.onClose();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blueAccent,  // Fond du bouton bleu clair
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20),
              ),
              padding: EdgeInsets.symmetric(horizontal: 30, vertical: 12),
            ),
            child: Text('Upload', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}
