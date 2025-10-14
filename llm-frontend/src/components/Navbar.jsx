import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import Tooltip from '@mui/material/Tooltip';
import AccountCircle from '@mui/icons-material/AccountCircle';
import Settings from '@mui/icons-material/Settings';
import Logout from '@mui/icons-material/Logout';
import Login from '@mui/icons-material/Login';
import Button from '@mui/material/Button';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ onMenuClick }) {
  const [hoveredItem, setHoveredItem] = useState(null);
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navItems = [
    { id: 'profile', icon: AccountCircle, label: 'Profile', action: () => navigate('/profile') },
    { id: 'options', icon: Settings, label: 'Options', action: () => navigate('/options') },
    { id: 'logout', icon: Logout, label: 'Logout', action: handleLogout }
  ];

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="fixed" color="primary" sx={{ zIndex: (theme) => theme.zIndex.drawer + 2 }}>
        <Toolbar>
          <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
            <Tooltip title="Menu" arrow>
              <Box
                sx={{
                  position: 'relative',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <IconButton
                  color="inherit"
                  aria-label="menu"
                  edge="start"
                  onClick={onMenuClick}
                  onMouseEnter={() => setHoveredItem('menu')}
                  onMouseLeave={() => setHoveredItem(null)}
                  sx={{
                    borderRadius: '20px',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    width: hoveredItem === 'menu' ? 'auto' : '40px',
                    minWidth: '40px',
                    height: '40px',
                    px: hoveredItem === 'menu' ? 2 : 1,
                    backgroundColor: hoveredItem === 'menu' ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                    backdropFilter: hoveredItem === 'menu' ? 'blur(10px)' : 'none',
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.15)',
                      transform: 'scale(1.05)'
                    },
                    '&:active': {
                      transform: 'scale(0.95)'
                    }
                  }}
                >
                  <MenuIcon sx={{ fontSize: '20px', mr: hoveredItem === 'menu' ? 1 : 0, transition: 'all 0.3s ease' }} />
                  <Typography
                    variant="body2"
                    sx={{
                      opacity: hoveredItem === 'menu' ? 1 : 0,
                      width: hoveredItem === 'menu' ? 'auto' : 0,
                      overflow: 'hidden',
                      whiteSpace: 'nowrap',
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      fontSize: '14px',
                      fontWeight: 500,
                      color: 'inherit',
                      transform: hoveredItem === 'menu' ? 'translateX(0)' : 'translateX(-20px)'
                    }}
                  >
                    Menu
                  </Typography>
                </IconButton>
              </Box>
            </Tooltip>
          </Box>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            eLIMSChat.ai POC
          </Typography>
          
          {/* User Navigation Icons or Login Button */}
          {token ? (
            <Box 
              sx={{ 
                display: 'flex', 
                alignItems: 'center',
                gap: 0,
                position: 'relative',
                zIndex: (theme) => theme.zIndex.drawer + 5
              }}
            >
              {navItems.map((item, index) => {
                const IconComponent = item.icon;
                const isHovered = hoveredItem === item.id;
                const shouldSlideLeft = hoveredItem && navItems.findIndex(nav => nav.id === hoveredItem) > index;
                
                return (
                  <Box
                    key={item.id}
                    sx={{
                      position: 'relative',
                      display: 'flex',
                      alignItems: 'center',
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      transform: shouldSlideLeft ? 'translateX(-40px)' : 'translateX(0)',
                      zIndex: isHovered ? (theme) => theme.zIndex.drawer + 10 : 1,
                    }}
                  >
                    <IconButton
                      color="inherit"
                      onClick={item.action}
                      onMouseEnter={() => setHoveredItem(item.id)}
                      onMouseLeave={() => setHoveredItem(null)}
                      sx={{
                        position: 'relative',
                        overflow: 'hidden',
                        borderRadius: '20px',
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        width: isHovered ? 'auto' : '40px',
                        minWidth: '40px',
                        height: '40px',
                        px: isHovered ? 2 : 1,
                        mr: isHovered ? 1 : 0,
                        backgroundColor: isHovered ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                        backdropFilter: isHovered ? 'blur(10px)' : 'none',
                        '&:hover': {
                          backgroundColor: 'rgba(255, 255, 255, 0.15)',
                          transform: 'scale(1.05)',
                        },
                        '&:active': {
                          transform: 'scale(0.95)',
                        }
                      }}
                    >
                      <IconComponent 
                        sx={{ 
                          fontSize: '20px',
                          transition: 'all 0.3s ease',
                          mr: isHovered ? 1 : 0,
                        }} 
                      />
                      <Typography
                        variant="body2"
                        sx={{
                          opacity: isHovered ? 1 : 0,
                          width: isHovered ? 'auto' : 0,
                          overflow: 'hidden',
                          whiteSpace: 'nowrap',
                          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                          fontSize: '14px',
                          fontWeight: 500,
                          color: 'inherit',
                          transform: isHovered ? 'translateX(0)' : 'translateX(-20px)',
                        }}
                      >
                        {item.label}
                      </Typography>
                    </IconButton>
                  </Box>
                );
              })}
            </Box>
          ) : (
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Box
                sx={{
                  position: 'relative',
                  display: 'flex',
                  alignItems: 'center',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  zIndex: 1,
                }}
              >
                <IconButton
                  color="inherit"
                  component={Link}
                  to="/login"
                  onMouseEnter={() => setHoveredItem('login')}
                  onMouseLeave={() => setHoveredItem(null)}
                  sx={{
                    position: 'relative',
                    overflow: 'hidden',
                    borderRadius: '20px',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    width: hoveredItem === 'login' ? 'auto' : '40px',
                    minWidth: '40px',
                    height: '40px',
                    px: hoveredItem === 'login' ? 2 : 1,
                    mr: hoveredItem === 'login' ? 1 : 0,
                    backgroundColor: hoveredItem === 'login' ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                    backdropFilter: hoveredItem === 'login' ? 'blur(10px)' : 'none',
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.15)',
                      transform: 'scale(1.05)',
                    },
                    '&:active': {
                      transform: 'scale(0.95)',
                    }
                  }}
                >
                  <Login 
                    sx={{ 
                      fontSize: '20px',
                      transition: 'all 0.3s ease',
                      mr: hoveredItem === 'login' ? 1 : 0,
                      color: 'white',
                    }} 
                  />
                  <Typography
                    variant="body2"
                    sx={{
                      opacity: hoveredItem === 'login' ? 1 : 0,
                      width: hoveredItem === 'login' ? 'auto' : 0,
                      overflow: 'hidden',
                      whiteSpace: 'nowrap',
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      fontSize: '14px',
                      fontWeight: 500,
                      color: 'white',
                      transform: hoveredItem === 'login' ? 'translateX(0)' : 'translateX(-20px)',
                    }}
                  >
                    Login
                  </Typography>
                </IconButton>
              </Box>
            </Box>
          )}
        </Toolbar>
      </AppBar>
    </Box>
  );
}
