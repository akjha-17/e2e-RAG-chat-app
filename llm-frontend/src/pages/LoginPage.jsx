import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Container, Typography, Paper, Box, TextField, Button, Alert, 
  Tabs, Tab, Divider, Chip
} from '@mui/material';
import { getDevToken, loginUser, registerUser } from '../api';

export default function LoginPage({ redirectPath = '/' }) {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();

  // Login form state
  const [loginData, setLoginData] = useState({
    username: '',
    password: ''
  });

  // Registration form state
  const [registerData, setRegisterData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    preferred_name: '',
    role: 'Research Analyst',
    organization: 'Research & Development'
  });

  // Dev login state
  const [devUsername, setDevUsername] = useState('');

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setError('');
    setSuccess('');
  };

  const handleLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await loginUser(loginData);
      login(res.data.access_token, res.data.user);
      navigate(redirectPath, { replace: true });
    } catch (e) {
      setError(e.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    if (registerData.password !== registerData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const res = await registerUser({
        username: registerData.username,
        email: registerData.email,
        password: registerData.password,
        full_name: registerData.full_name,
        preferred_name: registerData.preferred_name,
        role: registerData.role,
        organization: registerData.organization
      });
      login(res.data.access_token, res.data.user);
      navigate(redirectPath, { replace: true });
    } catch (e) {
      setError(e.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDevLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getDevToken(devUsername);
      login(res.data.access_token);
      navigate(redirectPath, { replace: true });
    } catch (e) {
      setError(e.response?.data?.detail || 'Dev login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 4, borderRadius: 4 }}>
        <Typography variant="h4" gutterBottom color="primary" align="center" sx={{ mb: 4 }}>
          ElimsChat AI
        </Typography>

        <Tabs value={tabValue} onChange={handleTabChange} centered sx={{ mb: 3 }}>
          <Tab label="Login" />
          <Tab label="Register" />
          <Tab label="Dev Login" />
        </Tabs>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

        {/* Login Tab */}
        {tabValue === 0 && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Username"
              value={loginData.username}
              onChange={e => setLoginData({...loginData, username: e.target.value})}
              disabled={loading}
              fullWidth
            />
            <TextField
              label="Password"
              type="password"
              value={loginData.password}
              onChange={e => setLoginData({...loginData, password: e.target.value})}
              disabled={loading}
              fullWidth
            />
            <Button
              variant="contained"
              onClick={handleLogin}
              disabled={loading || !loginData.username || !loginData.password}
              fullWidth
              size="large"
            >
              {loading ? 'Logging in...' : 'Login'}
            </Button>
            <Divider sx={{ my: 2 }} />
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Demo Accounts:
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
                <Chip 
                  label="admin / admin123"
                  size="small" 
                  onClick={() => setLoginData({username: 'admin', password: 'admin123'})}
                  clickable
                />
              </Box>
            </Box>
          </Box>
        )}

        {/* Register Tab */}
        {tabValue === 1 && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Username"
              value={registerData.username}
              onChange={e => setRegisterData({...registerData, username: e.target.value})}
              disabled={loading}
              fullWidth
              required
            />
            <TextField
              label="Email"
              type="email"
              value={registerData.email}
              onChange={e => setRegisterData({...registerData, email: e.target.value})}
              disabled={loading}
              fullWidth
              required
            />
            <TextField
              label="Full Name"
              value={registerData.full_name}
              onChange={e => setRegisterData({...registerData, full_name: e.target.value})}
              disabled={loading}
              fullWidth
              required
            />
            <TextField
              label="Preferred Name"
              value={registerData.preferred_name}
              onChange={e => setRegisterData({...registerData, preferred_name: e.target.value})}
              disabled={loading}
              fullWidth
              required
            />
            <TextField
              label="Role"
              value={registerData.role}
              onChange={e => setRegisterData({...registerData, role: e.target.value})}
              disabled={loading}
              fullWidth
            />
            <TextField
              label="Organization"
              value={registerData.organization}
              onChange={e => setRegisterData({...registerData, organization: e.target.value})}
              disabled={loading}
              fullWidth
            />
            <TextField
              label="Password"
              type="password"
              value={registerData.password}
              onChange={e => setRegisterData({...registerData, password: e.target.value})}
              disabled={loading}
              fullWidth
              required
            />
            <TextField
              label="Confirm Password"
              type="password"
              value={registerData.confirmPassword}
              onChange={e => setRegisterData({...registerData, confirmPassword: e.target.value})}
              disabled={loading}
              fullWidth
              required
            />
            <Button
              variant="contained"
              onClick={handleRegister}
              disabled={loading || !registerData.username || !registerData.password || !registerData.email}
              fullWidth
              size="large"
            >
              {loading ? 'Registering...' : 'Register'}
            </Button>
          </Box>
        )}

        {/* Dev Login Tab */}
        {tabValue === 2 && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Alert severity="info" sx={{ mb: 2 }}>
              Development mode - simplified authentication for testing
            </Alert>
            <TextField
              label="Username"
              value={devUsername}
              onChange={e => setDevUsername(e.target.value)}
              disabled={loading}
              fullWidth
            />
            <Button
              variant="contained"
              onClick={handleDevLogin}
              disabled={loading || !devUsername}
              fullWidth
              size="large"
            >
              {loading ? 'Logging in...' : 'Dev Login'}
            </Button>
            <Divider sx={{ my: 2 }} />
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Quick Access:
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
                <Chip 
                  label="admin"
                  size="small" 
                  onClick={() => setDevUsername('admin')}
                  clickable
                />
                <Chip 
                  label="user"
                  size="small" 
                  onClick={() => setDevUsername('user')}
                  clickable
                />
              </Box>
            </Box>
          </Box>
        )}
      </Paper>
    </Container>
  );
}