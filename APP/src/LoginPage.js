// import React, { useState, useEffect } from "react";
// import axios from "axios";
// import TextField from "@mui/material/TextField";
// import Button from "@mui/material/Button";
// import Box from "@mui/material/Box";
// import { createTheme, ThemeProvider } from "@mui/material/styles";

// const LoginPage = ({ onLogin }) => {
//   const [ip, setIp] = useState("");

//   useEffect(() => {
//     const fetchIp = async () => {
//       try {
//         const response = await axios.get("http://localhost:5000/api/ip");
//         console.log("Réponse IP :", response.data);
//         setIp(response.data.ip);
//       } catch (error) {
//         console.error("Erreur lors de la récupération de l'adresse IP :", error);
//       }
//     };

//     fetchIp();
//   }, []);

//   const handleLogin = async () => {
//     if (ip) {
//       try {
//         // Envoi de la requête pour rejoindre le réseau avec l'adresse IP
//         const response = await axios.post("http://localhost:5000/join_network", {
//           ip: ip,
//         });
//         console.log("Réponse du serveur:", response.data);
//         onLogin(ip);
//       } catch (error) {
//         console.error("Erreur lors de la connexion au réseau :", error);
//         alert("Erreur lors de la tentative de connexion au réseau.");
//       }
//     } else {
//       alert("Veuillez entrer une adresse IP.");
//     }
//   };

//   const theme = createTheme({
//     components: {
//       MuiTextField: {
//         styleOverrides: {
//           root: {
//             "& .MuiInputBase-input": {
//               color: "white",
//             },
//             "& .MuiInputLabel-root": {
//               color: "white",
//             },
//             "& .MuiInput-underline:before": {
//               borderBottomColor: "white",
//             },
//             "&:hover .MuiInput-underline:before": {
//               borderBottomColor: "lightgray",
//             },
//             "& fieldset": {
//               borderColor: "white",
//             },
//             "&:hover fieldset": {
//               borderColor: "lightgray",
//             },
//             "&.Mui-focused fieldset": {
//               borderColor: "blue",
//             },
//           },
//         },
//       },
//     },
//   });

//   return (
//     <Box
//       sx={{
//         height: "100vh",
//         display: "flex",
//         flexDirection: "column",
//         justifyContent: "center",
//         alignItems: "center",
//         backgroundColor: "#1a1a1a",
//         color: "#d9d9d9",
//       }}
//     >
//       <h2>Connexion au Réseau</h2>
//       <ThemeProvider theme={theme}>
//         <TextField
//           label="Adresse IP"
//           variant="outlined"
//           value={ip}
//           onChange={(e) => setIp(e.target.value)}
//           sx={{ marginBottom: 2, input: { color: "#d9d9d9" } }}
//         />
//       </ThemeProvider>

//       <Button variant="contained" onClick={handleLogin}>
//         Se Connecter
//       </Button>
//     </Box>
//   );
// };

// export default LoginPage;


import React, { useState } from "react";
import axios from "axios";

function PeerControl() {
  const [peerPort, setPeerPort] = useState("");
  const [activePeers, setActivePeers] = useState([]);
  const [message, setMessage] = useState("");

  const joinNetwork = async () => {
    try {
      const response = await axios.post("http://localhost:5000/join", { peer_port: peerPort });
      setActivePeers(response.data.active_peers);
      setMessage("Successfully joined the network.");
    } catch (error) {
      setMessage("Failed to join the network.");
    }
  };

  const leaveNetwork = async () => {
    try {
      await axios.post("http://localhost:5000/leave", { peer_port: peerPort });
      setActivePeers([]);
      setMessage("Successfully left the network.");
    } catch (error) {
      setMessage("Failed to leave the network.");
    }
  };

  const fetchPeers = async () => {
    try {
      const response = await axios.get("http://localhost:5000/peers");
      setActivePeers(response.data.active_peers);
    } catch (error) {
      setMessage("Failed to fetch active peers.");
    }
  };

  return (
    <div>
      <h2>Peer Control</h2>
      <input
        type="number"
        value={peerPort}
        onChange={(e) => setPeerPort(e.target.value)}
        placeholder="Enter port"
      />
      <button onClick={joinNetwork}>Join Network</button>
      <button onClick={leaveNetwork}>Leave Network</button>
      <button onClick={fetchPeers}>Fetch Active Peers</button>

      <div>
        <h3>Message: {message}</h3>
        <h3>Active Peers:</h3>
        <ul>
          {activePeers.map((peer, index) => (
            <li key={index}>{peer}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default PeerControl;

