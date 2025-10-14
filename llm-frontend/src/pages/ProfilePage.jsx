import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Box,
  Avatar,
  Chip,
  Alert,
  IconButton,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';

import {
  Person as PersonIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Email as EmailIcon,
  Business as BusinessIcon,
  Security as SecurityIcon,
  Lock as LockIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  BarChart as BarChartIcon,
  History as HistoryIcon,
  Chat as ChatIcon,
  Upload as UploadIcon,
  Download as DownloadIcon,
  Feedback as FeedbackIcon,
  Close as CloseIcon,
  Check as CheckIcon
} from '@mui/icons-material';

import { useAuth } from '../context/AuthContext';
import { updateUserProfile, getUserStats } from '../api';

export default function ProfilePage() {
  const { user, updateUser, token } = useAuth();
  
  const [profile, setProfile] = useState({
    puid: user?.puid || 'P123456',
    full_name: user?.full_name || 'User',
    preferred_name: user?.preferred_name || 'User',
    email: user?.email || 'user@company.com',
    role: user?.role || 'User',
    organization: user?.organization || 'Organization'
  });

  // Update profile when user changes (from AuthContext)
  useEffect(() => {
    if (user) {
      setProfile({
        puid: user.puid || 'P123456',
        full_name: user.full_name || 'User',
        preferred_name: user.preferred_name || 'User',
        email: user.email || 'user@company.com',
        role: user.role || 'User',
        organization: user.organization || 'Organization'
      });
    }
  }, [user]);

  const [editMode, setEditMode] = useState(false);
  const [editedProfile, setEditedProfile] = useState(profile);
  const [saved, setSaved] = useState(false);
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [profileDialogOpen, setProfileDialogOpen] = useState(false);
  const [passwordChanged, setPasswordChanged] = useState(false);

  // Password validation functions
  const validatePassword = (password) => {
    return {
      hasLowercase: /[a-z]/.test(password),
      hasUppercase: /[A-Z]/.test(password),
      hasNumber: /\d/.test(password),
      hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password),
      hasMinLength: password.length >= 8
    };
  };

  const isPasswordValid = (password) => {
    const validation = validatePassword(password);
    return Object.values(validation).every(Boolean);
  };

  // Activity stats - fetched from backend API
  const [activityStats, setActivityStats] = useState([
    { label: 'Total Chats', value: 'Loading...', icon: <ChatIcon color="primary" /> },
    { label: 'Documents Viewed', value: 'Loading...', icon: <UploadIcon color="secondary" /> },
    { label: 'Total Messages', value: 'Loading...', icon: <DownloadIcon color="success" /> },
    { label: 'Feedback Given', value: 'Loading...', icon: <FeedbackIcon color="warning" /> }
  ]);

  // Load user activity stats from API
  useEffect(() => {
    const loadUserStats = async () => {
      try {
        const response = await getUserStats(token);
        const stats = response.data;
        
        setActivityStats([
          { label: 'Total Chats', value: stats.total_chats.toString(), icon: <ChatIcon color="primary" /> },
          { label: 'Documents Viewed', value: stats.documents_viewed.toString(), icon: <UploadIcon color="secondary" /> },
          { label: 'Total Messages', value: stats.total_messages.toString(), icon: <DownloadIcon color="success" /> },
          { label: 'Feedback Given', value: stats.feedback_given.toString(), icon: <FeedbackIcon color="warning" /> }
        ]);
      } catch (error) {
        console.error('Failed to load user stats:', error);
        // Keep loading state or show error state
        setActivityStats([
          { label: 'Total Chats', value: 'Error', icon: <ChatIcon color="primary" /> },
          { label: 'Documents Viewed', value: 'Error', icon: <UploadIcon color="secondary" /> },
          { label: 'Total Messages', value: 'Error', icon: <DownloadIcon color="success" /> },
          { label: 'Feedback Given', value: 'Error', icon: <FeedbackIcon color="warning" /> }
        ]);
      }
    };

    if (user && token) {
      loadUserStats();
    }
  }, [user, token]);

  // Recent activity - fetched from backend API
  const [recentActivity, setRecentActivity] = useState([]);

  useEffect(() => {
    const loadRecentActivity = async () => {
      try {
        const response = await getUserStats(token);
        const stats = response.data;
        
        if (stats.recent_activity && stats.recent_activity.length > 0) {
          setRecentActivity(stats.recent_activity);
        } else {
          setRecentActivity([
            { action: 'Welcome to ElimsChat AI!', time: 'Just now' }
          ]);
        }
      } catch (error) {
        console.error('Failed to load recent activity:', error);
        setRecentActivity([
          { action: 'Unable to load recent activity', time: 'Error' }
        ]);
      }
    };

    if (user && token) {
      loadRecentActivity();
    }
  }, [user, token]);

  // Password state
  const lastPasswordUpdate = new Date(Date.now() - 91 * 24 * 60 * 60 * 1000); // 45 days ago
  const daysSinceUpdate = Math.floor((new Date() - lastPasswordUpdate) / (1000 * 60 * 60 * 24));
  const passwordExpired = daysSinceUpdate > 90;

  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const passwordsMatch = passwordForm.newPassword === passwordForm.confirmPassword && passwordForm.confirmPassword !== '';
  const allPasswordRequirementsMet = isPasswordValid(passwordForm.newPassword) && passwordsMatch && passwordForm.currentPassword !== '';

  const handleEdit = () => {
    setEditedProfile(profile);
    setProfileDialogOpen(true);
  };

  const handleSave = async () => {
    try {
      // Update profile via API
      await updateUserProfile({
        email: editedProfile.email,
        preferred_name: editedProfile.preferred_name
      }, token);
      
      setProfile(editedProfile);
      updateUser(editedProfile);  // Update AuthContext
      setProfileDialogOpen(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error('Failed to update profile:', error);
      // Handle error - you might want to show an error message
    }
  };

  const handleCancel = () => {
    setProfileDialogOpen(false);
    setEditedProfile(profile);
  };

  const handleChange = (field) => (event) => {
    setEditedProfile(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handlePasswordChange = (field) => (event) => {
    setPasswordForm(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handlePasswordSubmit = () => {
    console.log('Password change submitted');
    setPasswordDialogOpen(false);
    setPasswordChanged(true);
    setPasswordForm({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    });
    setTimeout(() => setPasswordChanged(false), 3000);
  };

  return (
    <Box sx={{ width: '100%', minHeight: '100vh', py: '2%' }}>
      <Container sx={{ width: '95%', maxWidth: 'none', margin: '0 auto', p: 0 }}>
        {/* Page Header */}
        <Typography variant="h4" sx={{ fontWeight: 600, mb: '3%', textAlign: 'left' }}>
          User Profile
        </Typography>
        
        {saved && (
          <Alert severity="success" sx={{ mb: '2%', width: '100%' }}>
            Profile updated successfully!
          </Alert>
        )}
        
        {passwordChanged && (
          <Alert severity="success" sx={{ mb: '2%', width: '100%' }}>
            Password updated successfully!
          </Alert>
        )}

        <Box sx={{ width: '100%' }}>
          {/* Profile Information Card */}
          <Card elevation={2} sx={{ mb: '3%', width: '100%' }}>
            <CardContent sx={{ p: '3%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: '2%' }}>
                <PersonIcon color="primary" sx={{ mr: '1%' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Profile Information
                </Typography>
              </Box>
              <Divider sx={{ mb: '3%' }} />
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: '3%' }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Avatar
                    sx={{ width: '4rem', height: '4rem', mr: '4%', bgcolor: 'primary.main' }}
                  >
                    {profile.full_name.split(' ').map(n => n[0]).join('')}
                  </Avatar>
                  <Box>
                    <Typography variant="h5" sx={{ fontWeight: 600 }}>
                      {profile.full_name}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      {profile.role}
                    </Typography>
                  </Box>
                </Box>
                <Button
                  startIcon={<EditIcon />}
                  onClick={handleEdit}
                  variant="outlined"
                >
                  Edit Profile
                </Button>
              </Box>

              <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ mb: '3%' }}>
                  <TextField
                    fullWidth
                    label="Preferred Name"
                    value={profile.preferred_name}
                    disabled={true}
                    InputProps={{
                      startAdornment: <PersonIcon sx={{ mr: '2%', color: 'text.secondary' }} />
                    }}
                    sx={{
                      '& .MuiInputBase-input.Mui-disabled': {
                        WebkitTextFillColor: '#000000'
                      }
                    }}
                  />
                </Box>
                
                <Box>
                  <TextField
                    fullWidth
                    label="Email Address"
                    value={profile.email}
                    disabled={true}
                    InputProps={{
                      startAdornment: <EmailIcon sx={{ mr: '2%', color: 'text.secondary' }} />
                    }}
                    sx={{
                      '& .MuiInputBase-input.Mui-disabled': {
                        WebkitTextFillColor: '#000000'
                      }
                    }}
                  />
                </Box>
                
                {/* Separator between editable and fixed fields */}
                <Divider sx={{ my: '3%' }} />
                
                <Box sx={{ mb: '3%' }}>
                  <TextField
                    fullWidth
                    label="PUID"
                    value={profile.puid}
                    disabled={true}
                    InputProps={{
                      startAdornment: <PersonIcon sx={{ mr: '2%', color: 'text.secondary' }} />
                    }}
                    sx={{
                      '& .MuiInputBase-input.Mui-disabled': {
                        WebkitTextFillColor: '#000000'
                      }
                    }}
                  />
                </Box>
                
                <Box sx={{ mb: '3%' }}>
                  <TextField
                    fullWidth
                    label="Full Name"
                    value={profile.full_name}
                    disabled={true}
                    InputProps={{
                      startAdornment: <PersonIcon sx={{ mr: '2%', color: 'text.secondary' }} />
                    }}
                    sx={{
                      '& .MuiInputBase-input.Mui-disabled': {
                        WebkitTextFillColor: '#000000'
                      }
                    }}
                  />
                </Box>
                
                <Box sx={{ mb: '3%' }}>
                  <TextField
                    fullWidth
                    label="Role"
                    value={profile.role}
                    disabled={true}
                    sx={{
                      '& .MuiInputBase-input.Mui-disabled': {
                        WebkitTextFillColor: '#000000'
                      }
                    }}
                  />
                </Box>
                
                <Box sx={{ mb: '3%' }}>
                  <TextField
                    fullWidth
                    label="Organization"
                    value={profile.organization}
                    disabled={true}
                    InputProps={{
                      startAdornment: <BusinessIcon sx={{ mr: '2%', color: 'text.secondary' }} />
                    }}
                    sx={{
                      '& .MuiInputBase-input.Mui-disabled': {
                        WebkitTextFillColor: '#000000'
                      }
                    }}
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* Security Section */}
          <Card elevation={2} sx={{ mb: '3%', width: '100%' }}>
            <CardContent sx={{ p: '3%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: '2%' }}>
                <SecurityIcon color="primary" sx={{ mr: '1%' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Security
                </Typography>
              </Box>
              <Divider sx={{ mb: '3%' }} />
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: '2%', bgcolor: 'grey.50', borderRadius: 2 }}>
                <Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    Password Security
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Last updated {daysSinceUpdate} days ago
                  </Typography>
                  {passwordExpired && (
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: '1%' }}>
                      <WarningIcon color="warning" sx={{ fontSize: 26, mr: '5%' }} />
                      <Typography variant="body2" color="warning.main">
                        Expired Password
                      </Typography>
                    </Box>
                  )}
                </Box>
                <Button
                  variant="outlined"
                  startIcon={<LockIcon />}
                  onClick={() => {
                    setPasswordForm({
                      currentPassword: '',
                      newPassword: '',
                      confirmPassword: ''
                    });
                    setPasswordDialogOpen(true);
                  }}
                  color={passwordExpired ? "warning" : "primary"}
                >
                  Change Password
                </Button>
              </Box>
            </CardContent>
          </Card>

          {/* Activity Stats Card */}
          <Card elevation={2} sx={{ mb: '3%', width: '100%' }}>
            <CardContent sx={{ p: '3%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: '2%' }}>
                <BarChartIcon color="primary" sx={{ mr: '1%' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Activity Stats
                </Typography>
              </Box>
              <Divider sx={{ mb: '3%' }} />
              <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column', 
                gap: '3%'
              }}>
                {activityStats.map((stat, index) => (
                  <Box
                    key={index}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      py: '1%',
                      width: '100%'
                    }}
                  >
                    <Box sx={{ mr: '3%' }}>
                      {stat.icon}
                    </Box>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        {stat.label}
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {stat.value}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>

          {/* Recent Activity Card */}
          <Card elevation={2} sx={{ width: '100%' }}>
            <CardContent sx={{ p: '3%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: '2%' }}>
                <HistoryIcon color="primary" sx={{ mr: '1%' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Recent Activity
                </Typography>
              </Box>
              <Divider sx={{ mb: '3%' }} />
              <Box sx={{ 
                overflowY: 'auto',
                maxHeight: '30vh',
                width: '100%',
                '&::-webkit-scrollbar': {
                  width: '0.8%',
                },
                '&::-webkit-scrollbar-track': {
                  background: '#f1f1f1',
                  borderRadius: '0.4%',
                },
                '&::-webkit-scrollbar-thumb': {
                  background: '#c1c1c1',
                  borderRadius: '0.4%',
                },
                '&::-webkit-scrollbar-thumb:hover': {
                  background: '#a8a8a8',
                },
                scrollbarWidth: 'thin',
                scrollbarColor: '#c1c1c1 #f1f1f1'
              }}>
                <List dense sx={{ width: '100%' }}>
                  {recentActivity.map((activity, index) => (
                    <ListItem
                      key={index}
                      sx={{
                        px: 0,
                        py: '1%',
                        borderBottom: index < recentActivity.length - 1 ? '1px solid' : 'none',
                        borderBottomColor: 'grey.100',
                        width: '100%'
                      }}
                    >
                      <ListItemText
                        primary={activity.action}
                        secondary={activity.time}
                        primaryTypographyProps={{ variant: 'body2' }}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Container>

      {/* Password Change Dialog */}
      <Dialog open={passwordDialogOpen} onClose={() => setPasswordDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: '2%', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ mb: '4%' }}>
              <TextField
                fullWidth
                label="Current Password"
                type="password"
                value={passwordForm.currentPassword}
                onChange={handlePasswordChange('currentPassword')}
              />
            </Box>
            <Box sx={{ mb: '4%' }}>
              <TextField
                fullWidth
                label="New Password"
                type="password"
                value={passwordForm.newPassword}
                onChange={handlePasswordChange('newPassword')}
              />
            </Box>
            
            {/* Password Requirements */}
            <Box sx={{ my: '4%' }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: '2%' }}>
                Password Requirements:
              </Typography>
              <List dense sx={{ py: 0 }}>
                {[
                  { key: 'hasLowercase', text: 'Password must contain at least 1 lower-case alphabet' },
                  { key: 'hasUppercase', text: 'Password must contain at least 1 upper-case alphabet' },
                  { key: 'hasNumber', text: 'Password must contain at least 1 number' },
                  { key: 'hasSpecialChar', text: 'Password must contain at least 1 special character' },
                  { key: 'hasMinLength', text: 'Password must be at least 8 characters long' }
                ].map((requirement) => {
                  const validation = validatePassword(passwordForm.newPassword);
                  const isValid = validation[requirement.key];
                  return (
                    <ListItem key={requirement.key} sx={{ py: '0.5%', px: 0 }}>
                      <ListItemIcon sx={{ minWidth: '5%' }}>
                        {isValid ? (
                          <CheckIcon sx={{ color: 'success.main', fontSize: 18 }} />
                        ) : (
                          <CloseIcon sx={{ color: 'error.main', fontSize: 18 }} />
                        )}
                      </ListItemIcon>
                      <ListItemText 
                        primary={requirement.text}
                        primaryTypographyProps={{ 
                          variant: 'body2',
                          sx: { color: isValid ? 'success.main' : 'error.main' }
                        }}
                      />
                    </ListItem>
                  );
                })}
              </List>
            </Box>

            <Box sx={{ mb: '4%' }}>
              <TextField
                fullWidth
                label="Confirm New Password"
                type="password"
                value={passwordForm.confirmPassword}
                onChange={handlePasswordChange('confirmPassword')}
              />
            </Box>
            
            {/* Password Match Validation */}
            <Box sx={{ mt: '2%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                {passwordsMatch ? (
                  <CheckIcon sx={{ color: 'success.main', fontSize: 18, mr: '1%' }} />
                ) : (
                  <CloseIcon sx={{ color: 'error.main', fontSize: 18, mr: '1%' }} />
                )}
                <Typography 
                  variant="body2" 
                  sx={{ color: passwordsMatch ? 'success.main' : 'error.main' }}
                >
                  Must match the New Password
                </Typography>
              </Box>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: '3%' }}>
          <Button onClick={() => setPasswordDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handlePasswordSubmit} 
            variant="contained"
            disabled={!allPasswordRequirementsMet}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Profile Edit Dialog */}
      <Dialog open={profileDialogOpen} onClose={handleCancel} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Profile</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: '2%', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ mb: '4%' }}>
              <TextField
                fullWidth
                label="Preferred Name"
                value={editedProfile.preferred_name}
                onChange={handleChange('preferred_name')}
                InputProps={{
                  startAdornment: <PersonIcon sx={{ mr: '2%', color: 'text.secondary' }} />
                }}
              />
            </Box>
            
            <Box sx={{ mb: '4%' }}>
              <TextField
                fullWidth
                label="Email Address"
                value={editedProfile.email}
                onChange={handleChange('email')}
                InputProps={{
                  startAdornment: <EmailIcon sx={{ mr: '2%', color: 'text.secondary' }} />
                }}
              />
            </Box>

            {/* Read-only fields for reference */}
            <Divider sx={{ my: '3%' }} />
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: '3%' }}>
              Read-only Information
            </Typography>
            
            <Box sx={{ mb: '3%' }}>
              <TextField
                fullWidth
                label="PUID"
                value={editedProfile.puid}
                disabled={true}
                size="small"
                InputProps={{
                  startAdornment: <PersonIcon sx={{ mr: '2%', color: 'text.secondary' }} />
                }}
              />
            </Box>
            
            <Box sx={{ mb: '3%' }}>
              <TextField
                fullWidth
                label="Full Name"
                value={editedProfile.full_name}
                disabled={true}
                size="small"
                InputProps={{
                  startAdornment: <PersonIcon sx={{ mr: '2%', color: 'text.secondary' }} />
                }}
              />
            </Box>
            
            <Box sx={{ mb: '3%' }}>
              <TextField
                fullWidth
                label="Role"
                value={editedProfile.role}
                disabled={true}
                size="small"
              />
            </Box>
            
            <Box sx={{ mb: '3%' }}>
              <TextField
                fullWidth
                label="Organization"
                value={editedProfile.organization}
                disabled={true}
                size="small"
                InputProps={{
                  startAdornment: <BusinessIcon sx={{ mr: '2%', color: 'text.secondary' }} />
                }}
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancel}>Cancel</Button>
          <Button onClick={handleSave} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}