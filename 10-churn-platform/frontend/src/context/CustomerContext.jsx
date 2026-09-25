import React, { createContext, useContext, useState, useEffect } from "react";
import { churnApi } from "../services/api";

const CustomerContext = createContext(null);

export function CustomerProvider({ children }) {
  const [targets, setTargets] = useState([]);
  const [activeCustomer, setActiveCustomer] = useState("Store Critical"); // specific customer or "ALL"
  const [isDataManagerOpen, setIsDataManagerOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  const refreshTargets = async () => {
    try {
      const data = await churnApi.getTargets();
      if (data.targets && data.targets.length > 0) {
        setTargets(data.targets);
        // If current active customer is not "ALL" and not in targets, select first
        if (activeCustomer !== "ALL" && !data.targets.some((t) => t.customer === activeCustomer)) {
          setActiveCustomer(data.targets[0].customer);
        }
      }
    } catch (e) {
      console.error("Failed to load targets:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshTargets();
  }, []);

  return (
    <CustomerContext.Provider
      value={{
        targets,
        activeCustomer,
        setActiveCustomer,
        isDataManagerOpen,
        setIsDataManagerOpen,
        refreshTargets,
        loading,
      }}
    >
      {children}
    </CustomerContext.Provider>
  );
}

export function useCustomer() {
  const ctx = useContext(CustomerContext);
  if (!ctx) throw new Error("useCustomer must be used within CustomerProvider");
  return ctx;
}
