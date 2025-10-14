import { createContext, useContext, useState, useEffect } from 'react';
import { getCurrentUser } from '../api';

const AuthContext = createContext();

// Helper function to decode JWT payload
const decodeJWT = (token) => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Error decoding JWT:', error);
    return null;
  }
};

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token') || '');
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [userRoles, setUserRoles] = useState(() => {
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      const payload = decodeJWT(savedToken);
      return payload?.roles || [];
    }
    return [];
  });

  // Load user data from token on mount
  useEffect(() => {
    const loadUserFromToken = async () => {
      if (token && !user) {
        try {
          const response = await getCurrentUser(token);
          const userData = response.data;
          setUser(userData);
          localStorage.setItem('user', JSON.stringify(userData));
          
          // Update roles from fresh token
          const payload = decodeJWT(token);
          const roles = payload?.roles || [];
          setUserRoles(roles);
        } catch (error) {
          console.error('Failed to load user data:', error);
          // If token is invalid, clear it
          logout();
        }
      }
    };

    loadUserFromToken();
  }, [token]);

  const login = (newToken, userData = null) => {
    setToken(newToken);
    localStorage.setItem('token', newToken);
    
    // Decode JWT to extract roles
    const payload = decodeJWT(newToken);
    const roles = payload?.roles || [];
    setUserRoles(roles);
    
    if (userData) {
      // If user data is provided (from login/register response), use it
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
    } else {
      // Extract user data from token for legacy dev tokens
      const tokenUserData = {
        id: payload?.user_id,
        username: payload?.sub,
        email: payload?.email || 'user@company.com',
        full_name: payload?.full_name || 'User',
        preferred_name: payload?.preferred_username || 'User',
        puid: payload?.puid || 'P000000',
        role: payload?.role || 'User',
        organization: payload?.organization || 'Organization',
        is_admin: roles.includes('admin')
      };
      setUser(tokenUserData);
      localStorage.setItem('user', JSON.stringify(tokenUserData));
    }
  };

  const logout = () => {
    setToken('');
    setUser(null);
    setUserRoles([]);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  const updateUser = (updatedUserData) => {
    setUser(updatedUserData);
    localStorage.setItem('user', JSON.stringify(updatedUserData));
  };

  // Helper functions to check roles
  const hasRole = (role) => userRoles.includes(role);
  const isAdmin = () => hasRole('admin');
  const isUser = () => hasRole('user');

  return (
    <AuthContext.Provider value={{ 
      token, 
      user, 
      userRoles, 
      login, 
      logout, 
      updateUser, 
      hasRole, 
      isAdmin, 
      isUser 
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}