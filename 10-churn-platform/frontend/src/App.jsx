import React, { useState } from "react";
import Sidebar, { MENUS } from "./components/Sidebar";
import Topbar from "./components/Topbar";
import ModelSettingsModal from "./components/ModelSettingsModal";
import DataManagerModal from "./components/DataManagerModal";
import { useCustomer } from "./context/CustomerContext";

// 9 Dedicated Menu Pages
import Menu01_PureML from "./pages/Menu01_PureML";
import Menu02_PureLLM from "./pages/Menu02_PureLLM";
import Menu03_Hybrid from "./pages/Menu03_Hybrid";
import Menu04_Agent from "./pages/Menu04_Agent";
import Menu05_Structured from "./pages/Menu05_Structured";
import Menu06_Guarded from "./pages/Menu06_Guarded";
import Menu07_Evals from "./pages/Menu07_Evals";
import Menu08_RAG from "./pages/Menu08_RAG";
import Menu09_LangGraphHITL from "./pages/Menu09_LangGraphHITL";

export default function App() {
  const [activeMenu, setActiveMenu] = useState("tier01");
  const { activeCustomer } = useCustomer();

  const currentMenu = MENUS.find((m) => m.id === activeMenu) || MENUS[0];

  const renderActivePage = () => {
    switch (activeMenu) {
      case "tier01":
        return <Menu01_PureML activeCustomer={activeCustomer} />;
      case "tier02":
        return <Menu02_PureLLM activeCustomer={activeCustomer} />;
      case "tier03":
        return <Menu03_Hybrid activeCustomer={activeCustomer} />;
      case "tier04":
        return <Menu04_Agent activeCustomer={activeCustomer} />;
      case "tier05":
        return <Menu05_Structured activeCustomer={activeCustomer} />;
      case "tier06":
        return <Menu06_Guarded activeCustomer={activeCustomer} />;
      case "tier07":
        return <Menu07_Evals activeCustomer={activeCustomer} />;
      case "tier08":
        return <Menu08_RAG activeCustomer={activeCustomer} />;
      case "tier09":
        return <Menu09_LangGraphHITL activeCustomer={activeCustomer} />;
      default:
        return <Menu01_PureML activeCustomer={activeCustomer} />;
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#fafafa] font-sans text-neutral-900">
      {/* 9-Menu Sidebar */}
      <Sidebar activeMenu={activeMenu} setActiveMenu={setActiveMenu} />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Topbar with Customer Selector & Active Model Chip */}
        <Topbar activeMenuTitle={`${currentMenu.number}. ${currentMenu.title}`} />

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto p-8">
          {renderActivePage()}
        </main>
      </div>

      {/* Dynamic Model Settings Modal */}
      <ModelSettingsModal />

      {/* Dynamic Dataset & Target Customer Manager Modal */}
      <DataManagerModal />
    </div>
  );
}
