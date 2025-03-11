import React, { useState } from "react";
// import * as React from 'react';
import backgroundImage from './assets/background2.jpg'; 
import myImage from './assets/dashboard.png';
import Button from '@mui/material/Button';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
// import { styled } from '@mui/material/styles';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import AccountBoxIcon from '@mui/icons-material/AccountBox';
import TextField from '@mui/material/TextField';
import { createTheme, ThemeProvider } from "@mui/material/styles";
import "./Page.css"
import axios from "axios";


const Page = ({ip,onLogout}) => {
  
  const pageStyle = {
    backgroundImage: `url(${backgroundImage})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
    height: '100vh',
    display: 'flex',
    flexDirection: 'column', // Organisation en colonne : en-tête et contenu
    justifyContent: 'center',
    alignItems: 'center',
    color: 'white',
    position: 'relative', // Nécessaire pour placer des éléments avec `absolute`
  };

  const headerStyle = {
    position: 'absolute', // Place le header en haut
    top: 0,
    right: 0,
    display: 'flex', // Les boutons sont côte à côte
    gap: '20px', // Espacement entre les conteneurs
    padding: '10px', // Espace autour des boutons
    borderRadius: '10px',
    background: '#212529'

  };

  const buttonContainerStyle = {
    display: 'flex',
    flexDirection: 'row', // Boutons côte à côte dans chaque conteneur
    gap: '10px', // Espacement entre les boutons
  };


  const contentContainerStyle = {
    backgroundColor: '#343a40', 
    color: 'black', // Couleur du texte
    width: '300px', // Largeur du conteneur
    padding: '20px', // Padding interne
    borderRadius: '10px', // Coins arrondis pour un effet visuel agréable
    position: 'absolute', // Permet de positionner le conteneur
    left: '3%', // Place le conteneur sur la gauche
    top: '50%', // Centre verticalement
    transform: 'translateY(-50%)', // Ajuste le décalage vertical
    boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.1)', // Ombre pour un effet esthétique
    alignItems: 'center',
    justifyContent: 'center', // Centre horizontalement
  };

  const contentStyle = {
    textAlign: 'center',
    alignItems: 'center',
    justifyContent: 'center',
  };

  const contentStyle2 = {
    textAlign: 'center',
    alignItems: 'center',
    justifyContent: 'center',
    color: "#d9d9d9",
  };

  const contentStyle3 = {
    textAlign: 'center',
    alignItems: 'center',
    justifyContent: 'center',
    color: "#d9d9d9",
  };

  //Theme des textfields
  const theme = createTheme({
    components: {
      MuiTextField: {
        styleOverrides: {
          root: {
            "& .MuiInputBase-input": {
              color: "white", // Couleur du texte
            },
            "& .MuiInputLabel-root": {
              color: "white", // Couleur du label
            },
            "& .MuiInput-underline:before": {
              borderBottomColor: "white", // Couleur de la ligne
            },
            "&:hover .MuiInput-underline:before": {
              borderBottomColor: "lightgray", // Ligne au survol
            },
          },
        },
      },
    },
  });

  // const handleFilenameChange = React.useCallback((e) => {
  //   setFilename(e.target.value);
  // }, []);

  

  function CustomTabPanel(props) {
    const { children, value, index, ...other } = props;
  
    return (
      <div
        role="tabpanel"
        hidden={value !== index}
        id={`simple-tabpanel-${index}`}
        aria-labelledby={`simple-tab-${index}`}
        {...other}
      >
        {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
      </div>
    );
  }
  
  CustomTabPanel.propTypes = {
    children: PropTypes.node,
    index: PropTypes.number.isRequired,
    value: PropTypes.number.isRequired,
  };
  
  function a11yProps(index) {
    return {
      id: `simple-tab-${index}`,
      'aria-controls': `simple-tabpanel-${index}`,
    };
  }

  const [value, setValue] = React.useState(0);

  const handleChange = (event, newValue) => {
    setValue(newValue);
  };

  // Partie pop up profil
  // State pour contrôler l'ouverture du popup
  const [isPopupOpen, setIsPopupOpen] = React.useState(false);
  const [isNetworkPopUpOpen, setIsNetworkPopupOpen] = React.useState(false);
  const [isNetworkInfoPopUpOpen, setIsInfoNetworkPopupOpen] = React.useState(false);
  // Fonction pour ouvrir ou fermer les popup
  const togglePopupProfile = () => {
    setIsPopupOpen(!isPopupOpen);
  };

  const togglePopupFileInNetwork = () => {
    setIsNetworkPopupOpen(!isNetworkPopUpOpen);
  };

  const togglePopupNetworkInfo = () => {
    setIsInfoNetworkPopupOpen(!isNetworkInfoPopUpOpen)
  };

  const overlayStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    backgroundColor: 'rgba(0, 0, 0, 0.5)', // Fond semi-transparent
    zIndex: 999, // S'assurer que le fond est derrière le popup
    display: isPopupOpen || isNetworkPopUpOpen  ? 'block' : 'none', // Affiche ou cache le fond
  };

  const popupStyleProfile = {
    position: 'fixed',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)', // Centrage
    width: '400px',
    padding: '20px',
    backgroundColor: '#343a40',
    boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.2)',
    zIndex: 1000, // S'assurer que le popup est au-dessus de l'overlay
    display: isPopupOpen  ? 'block' : 'none', // Affiche ou cache le popup
    opacity: isPopupOpen  ? 1 : 0, // Animation de fondu
    transition: 'opacity 0.3s ease', // Effet de fondu
  };

  const popupStyleNetwork = {
    color:"white",
    position: 'fixed',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)', // Centrage
    width: '400px',
    padding: '20px',
    backgroundColor: '#343a40',
    boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.2)',
    zIndex: 1000, // S'assurer que le popup est au-dessus de l'overlay
    display: isNetworkPopUpOpen  ? 'block' : 'none', // Affiche ou cache le popup
    opacity: isNetworkPopUpOpen  ? 1 : 0, // Animation de fondu
    transition: 'opacity 0.3s ease', // Effet de fondu
  };

  const popupStyleNetworkInfo = {
    position: 'fixed',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)', // Centrage
    width: '400px',
    padding: '20px',
    backgroundColor: '#343a40',
    boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.2)',
    zIndex: 1000, // S'assurer que le popup est au-dessus de l'overlay
    display: isNetworkInfoPopUpOpen ? 'block' : 'none', // Affiche ou cache le popup
    opacity: isNetworkInfoPopUpOpen ? 1 : 0, // Animation de fondu
    transition: 'opacity 0.3s ease', // Effet de fondu
  };
  
// contenu des pop ups
  const PopUpProfile = ( <>
    <p style={contentStyle3}> <AccountBoxIcon fontSize="large" /></p>
    <h2 style={contentStyle3}>IP: {ip}</h2>
    <p>Fichiers téléchargés: 2</p>
    <p>Fichiers uploads: 3</p>
    <p>Crédits: 10</p>
    <p>Recharger les Crédits</p>
    <Button variant ='contained' size='small' onClick={togglePopupProfile}>Close</Button>
    </>
  );

  const [files, setFiles] = useState([]); // État pour stocker les fichiers
  const [error, setError] = useState(null); // État pour les erreurs
  // eslint-disable-next-line
  const [loading, setLoading] = useState(false); // État pour indiquer le chargement

  const fetchFiles = async () => {
    try {
      const response = await axios.get("http://localhost:5000/api/files");
      setFiles(response.data.files); // Met à jour l'état avec la liste des fichiers
    } catch (err) {
      setError("Erreur lors de la récupération des fichiers.");
      console.error(err);
    } finally {
      setLoading(false); // Désactive l'indicateur de chargement
    }
  };

  const styleFindFile = {
    left: '20%',
  }

  const PopUpNetwork = (
    <>
      <h2 style={contentStyle2}>Rechercher un Fichier dans le réseau</h2>
      <ThemeProvider theme={theme} ><TextField  id="standard-basic" label="Search Field" variant="standard"/></ThemeProvider> 
      <SearchRoundedIcon fontSize="large"></SearchRoundedIcon>
      <Button style={styleFindFile} variant ='contained' size='small' padding='10px' onClick={fetchFiles}>Find Files</Button>
      <div>
      <h2>Liste des fichiers</h2>
      {error && <p style={{ color: "red" }}>{error}</p>}
      <ul>
        {files.length > 0 ? (
          files.map((file, index) => <li key={index}>{file}</li>)
        ) : (<p>Aucun fichier disponible.</p>)
        }
      </ul>
      </div>
      <Button variant ='contained' size='small' onClick={togglePopupFileInNetwork}>Close</Button>
        </>
  );

  // // eslint-disable-next-line
  const PopUpNetworkInfo = (
    <>
      <img src={myImage} alt="Network Information" style={{ width: '400px' }} />
      <Button
        variant="contained"
        size="small"
        onClick={togglePopupNetworkInfo}
        style={{ marginTop: '20px' }}
      >
        Close
      </Button>
    </>
  );

  const handlePrint = async () => {
    try {
      const response = await axios.get('http://localhost:5000/info');
      console.log(response.data);
    } catch (err) {
      console.error(err);
    }
  };

  // Upload
  // eslint-disable-next-line
    const [file,setFile] = useState(null);

    const handleFileChange = async (e) => {
      const selectedFile = e.target.files[0];
      if (!selectedFile) return;
  
      setFile(selectedFile);
  
      const formData = new FormData();
      formData.append("file", selectedFile);
  
      try {
        const response = await fetch("http://localhost:5000/upload", {
          method: "POST",
          body: formData,
        });
  
        if (response.ok) {
          alert("Fichier uploadé avec succès !");
        } else {
          alert("Erreur lors de l'upload.");
        }
      } catch (error) {
        console.error("Erreur:", error);
        alert("Impossible de se connecter au serveur.");
      }
    };

    // Download
  
    const [filename, setFilename] = useState("");

    const handleDownload = async () => {
      try {
        const response = await axios.post("http://localhost:5000/api/download", {
          filename: filename,
        });
  
        alert(response.data.message);
      } catch (error) {
        console.error("Erreur lors du téléchargement :", error);
        alert(error.response?.data?.error || "Une erreur est survenue");
      }
    };

    const handleLogout = async () => {
      try {
        const response = await axios.post("http://localhost:5000/leave", { ip });
        console.log("Réponse du serveur :", response.data);
      } catch (error) {
        console.error("Erreur lors de la déconnexion :", error);
      } finally {
        onLogout(); // S'exécute toujours, même en cas d'erreur
      }
    };

//Affichage app
  return (

<div className='pageStyle' style={pageStyle}>
      <h1>Bienvenue sur NodeLink !</h1>
      <h3>Connecté à : {ip}</h3>
      {/* Header en haut à droite */}
      <div style={headerStyle} className='headerStyle'>
        {/* Premier conteneur */}
        <div style={buttonContainerStyle} className='buttonContainerStyle'>
          <Button variant="contained" size = 'large' onClick={togglePopupFileInNetwork} sx={{color:'#d9d9d9', fontWeight:"bold",background: "#343a40"}}>Fichier dans le réseau</Button>
          <Button variant = "contained" size = 'large' onClick={handlePrint} sx={{color:'#d9d9d9', fontWeight:"bold",background: "#343a40"}}>Informations Réseau</Button>
        </div>
        {/* Deuxième conteneur */}
        <div style={buttonContainerStyle} className='buttonContainerStyle'>
          <Button variant ='contained' size = 'large' onClick={togglePopupProfile} sx={{color:'#d9d9d9', fontWeight:"bold",background: "#343a40"}}>Profil</Button>
          <Button variant="text" size = 'large' sx={{color:'#d9d9d9', fontWeight:"bold"}} onClick={handleLogout}>Déconnexion</Button>
          
        </div>
      </div>

      {/* Contenu dans l'encadré a gauche */}
      <div style={contentContainerStyle} className='contentContainerStyle'>
        <p >

            <Box  sx={{ borderBottom: 1, borderColor: 'divider',display: 'flex', alignItems: 'flex-end' }}>
                <Tabs value={value} onChange={handleChange} aria-label="basic tabs example">
                  <Tab label="Upload" {...a11yProps(0)} sx={{color:"#d9d9d9"}} />
                  <Tab label="Download" {...a11yProps(1)} sx={{color:"#d9d9d9"}} />
                </Tabs>
              </Box>

              <CustomTabPanel value={value} index={0}>
              <h1 style = {contentStyle2} className='contentStyle2'>Charger des Fichiers</h1>
              <p style ={contentStyle} className='contentStyle'>
              <div>
              <input type="file" onChange={handleFileChange} style={{ display: "none" }} id="file-input"/>
               <label htmlFor="file-input">
              <Button component="span" size="large" variant="contained" startIcon={<CloudUploadIcon />}>
              Upload
              </Button>
              </label>
              </div> </p> </CustomTabPanel>

              <CustomTabPanel value={value} index={1}>
                <h1 style = {contentStyle2} >Télécharger des Fichiers</h1>
                <ThemeProvider theme={theme} ><TextField  id="standard-basic" label="Search Field" variant="standard" value = {filename} onChange={(e)=> setFilename(e.target.value)} /></ThemeProvider>
                <Button component = "span" size = 'large' variant ='contained' onClick={handleDownload}>Download </Button>
              </CustomTabPanel>
              </p> </div>

    {/* Overlay qui assombrit le fond */}
    <div style={overlayStyle} onClick={(event)=> { 
      
      if (isPopupOpen) {
      setIsPopupOpen(false);
    }
    if (isNetworkPopUpOpen) {
      setIsNetworkPopupOpen(false);
    }}} />

    {/* Popup Profile*/}
    <div style={popupStyleProfile}>
      {PopUpProfile}
    </div>

    {/* Popup File in network*/}
    <div style={popupStyleNetwork}>
      {PopUpNetwork}
    </div>

    {/* Popup Network Info */}
    <div style={popupStyleNetworkInfo}>
      {PopUpNetworkInfo}
    </div>

</div>
  );
};

export default Page;
