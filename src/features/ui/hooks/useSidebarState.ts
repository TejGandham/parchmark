import { useState } from 'react';

export const useSidebarState = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return {
    isSidebarOpen,
    toggleSidebar,
  };
};
