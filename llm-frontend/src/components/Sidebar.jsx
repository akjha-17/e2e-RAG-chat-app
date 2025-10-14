import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  Box,
  Typography
} from '@mui/material';

import {
  Home as HomeIcon,
  Upload as UploadIcon,
  Refresh as RefreshIcon,
  Feedback as FeedbackIcon,
  HealthAndSafety as HealthIcon,
  Chat as ChatIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const drawerWidth = 240;

const menuGroups = [
  {
    title: 'Dashboard',
    items: [
      { text: 'Home', icon: <HomeIcon />, path: '/', public: true },
      { text: 'Health', icon: <HealthIcon />, path: '/health', public: true }
    ],
    requiredRole: null // Always visible
  },
  {
    title: 'AI Interaction',
    items: [
      { text: 'Chat with AI', icon: <ChatIcon />, path: '/ask', public: false },
      { text: 'Feedback', icon: <FeedbackIcon />, path: '/feedback', public: false }
    ],
    requiredRole: 'user' // Only visible if user has 'user' role
  },
  {
    title: 'Administration',
    items: [
      { text: 'Upload', icon: <UploadIcon />, path: '/upload', public: false },
      { text: 'Reindex', icon: <RefreshIcon />, path: '/reindex', public: false },
      { text: 'Analysis', icon: <AnalyticsIcon />, path: '/analysis', public: false }
    ],
    requiredRole: 'admin' // Only visible if user has 'admin' role
  }
];

function Sidebar({ open, onClose, variant = 'temporary' }) {
  const location = useLocation();
  const { token, hasRole } = useAuth();

  // Filter groups based on authentication and roles
  const getFilteredGroups = () => {
    return menuGroups.map(group => {
      // Check if the entire group should be visible based on role requirements
      const isGroupVisible = () => {
        if (!group.requiredRole) return true; // No role requirement, always visible
        if (!token) return false; // Not authenticated, hide groups with role requirements
        return hasRole(group.requiredRole); // Check if user has the required role
      };

      if (!isGroupVisible()) {
        return null; // Hide the entire group
      }

      // Filter items within the group based on authentication
      const filteredItems = group.items.filter(item => {
        if (item.public) return true; // Public items are always visible
        return token; // Private items require authentication
      });

      return {
        ...group,
        items: filteredItems
      };
    }).filter(group => group !== null && group.items.length > 0); // Only show groups that exist and have visible items
  };

  const filteredGroups = getFilteredGroups();

  const drawer = (
    <Box sx={{ overflow: 'auto' }}>
      <Divider />
      {filteredGroups.map((group, groupIndex) => (
        <Box key={group.title}>
          {/* Group Title */}
          <Box sx={{ px: 2, py: 1.5 }}>
            <Typography 
              variant="caption" 
              sx={{ 
                fontWeight: 600, 
                color: 'text.secondary',
                textTransform: 'uppercase',
                letterSpacing: 1
              }}
            >
              {group.title}
            </Typography>
          </Box>
          
          {/* Group Items */}
          <List sx={{ py: 0 }}>
            {group.items.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton
                  component={Link}
                  to={item.path}
                  selected={location.pathname === item.path}
                  onClick={variant === 'temporary' ? onClose : undefined}
                  sx={{
                    mx: 1,
                    borderRadius: 1,
                    '&.Mui-selected': {
                      backgroundColor: 'primary.light',
                      color: 'primary.contrastText',
                      '&:hover': {
                        backgroundColor: 'primary.main',
                      },
                      '& .MuiListItemIcon-root': {
                        color: 'inherit',
                      },
                    },
                  }}
                >
                  <ListItemIcon>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
          
          {/* Add divider between groups (except for the last group) */}
          {groupIndex < filteredGroups.length - 1 && (
            <Divider sx={{ my: 1 }} />
          )}
        </Box>
      ))}
    </Box>
  );

  return (
    <Drawer
      variant={variant}
      open={open}
      onClose={onClose}
      sx={{
        width: open ? drawerWidth : 0,
        flexShrink: 0,
        transition: 'width 0.3s',
        '& .MuiDrawer-paper': {
          width: open ? drawerWidth : 0,
          boxSizing: 'border-box',
          transition: 'width 0.3s',
          overflowX: 'hidden',
          // mt removed to eliminate whitespace
          height: { xs: 'calc(100% - 56px)', md: 'calc(100% - 64px)' },
          top: { xs: 56, md: 64 },
        },
      }}
    >
      {drawer}
    </Drawer>
  );
}

export default Sidebar;