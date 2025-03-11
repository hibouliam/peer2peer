import React, { useState } from "react";
import LoginPage from "./LoginPage";
import Page from "./Page";

const App = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [ip, setIp] = useState("");
  const [peerPort, setPeerPort] = useState("");

  const handleLogin = (enteredIp,enteredPort) => {
    setIp(enteredIp);
    setPeerPort(enteredPort);
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    setIp("");
    setIsLoggedIn(false);
  };

  return (
    <div>
      {isLoggedIn ? <Page ip={ip} peerPort={peerPort} onLogout={handleLogout} /> : <LoginPage onLogin={handleLogin} />}

    </div>
  );
};

export default App;
