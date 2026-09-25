import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import { SettingsProvider } from "./context/SettingsContext.jsx";
import { CustomerProvider } from "./context/CustomerContext.jsx";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <SettingsProvider>
      <CustomerProvider>
        <App />
      </CustomerProvider>
    </SettingsProvider>
  </React.StrictMode>
);
