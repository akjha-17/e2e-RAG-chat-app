import React, { createContext, useContext, useState } from 'react';

const SidebarContext = createContext();

export const SidebarProvider = ({ children }) => {
  const [mainSidebarOpen, setMainSidebarOpen] = useState(true);

  const toggleMainSidebar = () => {
    setMainSidebarOpen(prev => !prev);
  };

  return (
    <SidebarContext.Provider value={{
      mainSidebarOpen,
      setMainSidebarOpen,
      toggleMainSidebar
    }}>
      {children}
    </SidebarContext.Provider>
  );
};

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (context === undefined) {
    throw new Error('useSidebar must be used within a SidebarProvider');
  }
  return context;
};