import React from 'react';
import { Box, Toolbar, useTheme, useMediaQuery } from '@mui/material';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import { useSidebar } from '../context/SidebarContext';

const drawerWidth = 240;

function Layout({ children }) {
  const { mainSidebarOpen, toggleMainSidebar } = useSidebar();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Navbar onMenuClick={toggleMainSidebar} />
      
      <Box
        component="nav"
        sx={{ width: mainSidebarOpen ? { md: drawerWidth } : { md: 0 }, flexShrink: { md: 0 }, transition: 'width 0.3s' }}
      >
        <Sidebar
          variant={isMobile ? 'temporary' : 'persistent'}
          open={mainSidebarOpen}
          onClose={toggleMainSidebar}
        />
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: mainSidebarOpen ? { md: `calc(100% - ${drawerWidth}px)` } : { md: '100%' },
          backgroundColor: 'background.default',
          transition: 'width 0.3s',
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        <Toolbar />
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
}

export default Layout;