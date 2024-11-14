import 'package:flutter/material.dart';

class IconButtons extends StatelessWidget {
  final VoidCallback onUploadClick;

  IconButtons({required this.onUploadClick});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        IconButton(
          icon: Icon(Icons.upload_file, size: 50, color: Colors.blueGrey[200]),  // Icône upload blanche
          onPressed: onUploadClick,
        ),
        SizedBox(width: 20),
        IconButton(
          icon: Icon(Icons.download, size: 50, color: Colors.blueGrey[200]),  // Icône téléchargement blanche
          onPressed: () {
            print("Download button pressed");
          },
        ),
      ],
    );
  }
}
