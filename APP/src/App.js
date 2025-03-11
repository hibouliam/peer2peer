import React, { useState } from "react";
import LoginPage from "./LoginPage";
import Page from "./Page";

const App = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [ip, setIp] = useState("");

  const handleLogin = (enteredIp) => {
    setIp(enteredIp);
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    setIp("");
    setIsLoggedIn(false);
  };

  return (
    <div>
      {isLoggedIn ? <Page ip={ip} onLogout={handleLogout} /> : <LoginPage onLogin={handleLogin} />}
    </div>
  );
};

export default App;
