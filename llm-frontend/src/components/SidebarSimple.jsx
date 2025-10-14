import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Box,
  Typography
} from '@mui/material';
import { Link, useLocation } from 'react-router-dom';

const drawerWidth = 240;

const menuItems = [
  { text: 'Home', path: '/' },
  { text: 'Upload', path: '/upload' },
  { text: 'Reindex', path: '/reindex' },
  { text: 'Feedback', path: '/feedback' },
  { text: 'Health', path: '/health' },
  { text: 'Login', path: '/login' }
];

function Sidebar({ open, onClose, variant = 'temporary' }) {
  const location = useLocation();

  const drawer = (
    <Box sx={{ overflow: 'auto' }}>
      <Box sx={{ p: 2, minHeight: 64 }}>
        <Typography variant="h6" component="div" color="primary">
          LLM Chat
        </Typography>
      </Box>
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
              onClick={variant === 'temporary' ? onClose : undefined}
            >
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Drawer
      variant={variant}
      open={open}
      onClose={onClose}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      {drawer}
    </Drawer>
  );
}

export default Sidebar;