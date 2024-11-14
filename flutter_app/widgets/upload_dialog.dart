import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';

class UploadDialog extends StatefulWidget {
  final VoidCallback onClose;

  UploadDialog({required this.onClose});

  @override
  _UploadDialogState createState() => _UploadDialogState();
}

class _UploadDialogState extends State<UploadDialog> {
  TextEditingController _searchController = TextEditingController();
  bool _isUploadEnabled = false;
  bool _isPickingFile = false;  // Indicateur pour bloquer l'app pendant la sélection

  // Fonction pour ouvrir le sélecteur de fichiers
  Future<void> _pickFile() async {
    setState(() {
      _isPickingFile = true;  // Activer le mode de sélection de fichier
    });

    FilePickerResult? result = await FilePicker.platform.pickFiles();

    if (result != null) {
      String fileName = result.files.single.name;
      setState(() {
        _searchController.text = fileName;
        _isUploadEnabled = true;  // Activer le bouton "Upload"
        _isPickingFile = false;   // Désactiver le mode de sélection de fichier
      });
      print("File selected: $fileName");
    } else {
      setState(() {
        _isPickingFile = false;  // Désactiver le mode de sélection si annulé
      });
      print("No file selected");
    }
  }

  // Fonction pour gérer l'action d'upload
  void _handleUpload() {
    if (_isUploadEnabled) {
      widget.onClose();  // Fermer le dialogue uniquement si un fichier est sélectionné
    }
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Container(
          height: 200,
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.blueGrey[900],
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(20),
              topRight: Radius.circular(20),
            ),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                'Upload a document',
                style: TextStyle(color: Colors.white, fontSize: 18),
              ),
              SizedBox(height: 20),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 30),
                child: Row(
                  children: [
                    Expanded(
                      child: Container(
                        decoration: BoxDecoration(
                          color: Colors.blueGrey[600],
                          borderRadius: BorderRadius.circular(30),
                          border: Border.all(color: Colors.white),
                        ),
                        child: TextField(
                          controller: _searchController,
                          readOnly: false,
                          decoration: InputDecoration(
                            hintText: 'Search your document',
                            hintStyle: TextStyle(color: Colors.white54),
                            border: InputBorder.none,
                            contentPadding: EdgeInsets.symmetric(horizontal: 20),
                          ),
                          style: TextStyle(color: Colors.white),
                          onChanged: (value) {
                            if (!_isUploadEnabled) return;
                            setState(() {
                              _isUploadEnabled = false;
                            });
                          },
                        ),
                      ),
                    ),
                    SizedBox(width: 10),
                    Container(
                      decoration: BoxDecoration(
                        border: Border.all(
                          color: Colors.white,
                          width: 2,
                        ),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: IconButton(
                        icon: Icon(
                          Icons.folder_outlined,
                          color: Colors.white,
                          size: 30,
                        ),
                        onPressed: _isPickingFile ? null : _pickFile,  // Désactiver pendant sélection
                      ),
                    ),
                  ],
                ),
              ),
              SizedBox(height: 20),
              ElevatedButton(
                onPressed: _isUploadEnabled ? _handleUpload : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: _isUploadEnabled ? Colors.blueAccent : Colors.grey,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(20),
                  ),
                  padding: EdgeInsets.symmetric(horizontal: 30, vertical: 12),
                ),
                child: Text('Upload', style: TextStyle(color: Colors.white)),
              ),
            ],
          ),
        ),
        if (_isPickingFile)
        // Couche de blocage semi-transparente pendant la sélection
          Positioned.fill(
            child: Container(
              color: Colors.black.withOpacity(0.5),
            ),
          ),
      ],
    );
  }
}
