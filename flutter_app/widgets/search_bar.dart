import 'package:flutter/material.dart';

class CustomSearchBar extends StatelessWidget {
  final TextEditingController searchController;

  CustomSearchBar({required this.searchController});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 50),  // Abaisser la barre
      child: Container(
        padding: EdgeInsets.symmetric(horizontal: 20),
        decoration: BoxDecoration(
          color: Colors.grey[800],  // Couleur de fond
          borderRadius: BorderRadius.circular(30),  // Bords arrondis
          border: Border.all(color: Colors.blueGrey),  // Bordure noire
        ),
        child: Row(
          children: [
            // Barre de recherche à gauche
            Expanded(
              child: TextField(
                controller: searchController,
                decoration: InputDecoration(
                  hintText: 'Search your document',
                  hintStyle: TextStyle(color: Colors.white54),  // Texte transparent
                  border: InputBorder.none,  // Pas de bordure
                ),
                style: TextStyle(color: Colors.white),
              ),
            ),
            // Icône de recherche à droite
            IconButton(
              icon: Icon(Icons.search, color: Colors.white),
              onPressed: () {
                // Validation de la recherche
                print("Searching: ${searchController.text}");
              },
            ),
          ],
        ),
      ),
    );
  }
}
