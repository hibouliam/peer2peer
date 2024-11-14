import 'package:flutter/material.dart';
import '../widgets/search_bar.dart';
import '../widgets/icon_buttons.dart';
import '../widgets/upload_dialog.dart';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  TextEditingController _searchController = TextEditingController();
  bool _showDialog = false;

  void _showUploadDialog() {
    setState(() {
      _showDialog = true;
    });
  }

  void _closeUploadDialog() {
    setState(() {
      _showDialog = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,  // Fond sombre pour le thème dark
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            CustomSearchBar(
              searchController: _searchController,
            ),
            SizedBox(height: 20),
            IconButtons(
              onUploadClick: _showUploadDialog,
            ),
          ],
        ),
      ),
      bottomSheet: _showDialog ? UploadDialog(onClose: _closeUploadDialog) : null,
    );
  }
}
