import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Switch,
  FormGroup,
  FormControlLabel,
  Divider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Button,
  Alert,
  Card,
  CardContent,
  Grid
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Palette as PaletteIcon,
  Notifications as NotificationsIcon,
  Security as SecurityIcon,
  Language as LanguageIcon,
  Storage as StorageIcon
} from '@mui/icons-material';
import { useTheme } from '../context/ThemeContext';
import { useSettings } from '../context/SettingsContext';

export default function OptionsPage() {
  const { isDarkMode, toggleTheme } = useTheme();
  const { settings: appSettings, updateSetting, updateSettings } = useSettings();
  
  const [settings, setSettings] = useState({
    darkMode: isDarkMode,
    ...appSettings
  });

  const [saved, setSaved] = useState(false);

  // Sync with app settings
  useEffect(() => {
    setSettings(prev => ({
      ...prev,
      ...appSettings,
      darkMode: isDarkMode // Always use current theme state
    }));
  }, [appSettings, isDarkMode]);

  const handleSettingChange = (setting) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    
    // Handle dark mode toggle specially
    if (setting === 'darkMode') {
      toggleTheme();
      setSettings(prev => ({
        ...prev,
        [setting]: value
      }));
    } else {
      setSettings(prev => ({
        ...prev,
        [setting]: value
      }));
    }
  };

  const handleSliderChange = (setting) => (event, newValue) => {
    setSettings(prev => ({
      ...prev,
      [setting]: newValue
    }));
  };

  const handleSave = () => {
    // Save to app settings context (excludes darkMode which is handled separately)
    const { darkMode, ...appSettingsToSave } = settings;
    updateSettings(appSettingsToSave);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const settingSections = [
    {
      title: 'Appearance',
      icon: <PaletteIcon color="primary" />,
      settings: [
        {
          key: 'darkMode',
          label: 'Dark Mode',
          type: 'switch',
          description: 'Switch between light and dark themes'
        }
      ]
    },
    {
      title: 'Chat Settings',
      icon: <SettingsIcon color="primary" />,
      settings: [
        {
          key: 'responseLength',
          label: 'Response Length',
          type: 'slider',
          min: 10,
          max: 100,
          description: 'Preferred length of AI responses (percentage)'
        },
        {
          key: 'showSources',
          label: 'Show Sources',
          type: 'switch',
          description: 'Display source documents for answers'
        },
        {
          key: 'enableFeedback',
          label: 'Enable Feedback',
          type: 'switch',
          description: 'Allow rating and commenting on responses'
        },
        {
          key: 'cacheResponses',
          label: 'Cache Responses',
          type: 'switch',
          description: 'Store responses locally for faster access'
        }
      ]
    },
    {
      title: 'System',
      icon: <NotificationsIcon color="primary" />,
      settings: [
        {
          key: 'notifications',
          label: 'Notifications',
          type: 'switch',
          description: 'Enable browser notifications'
        },
        {
          key: 'autoSave',
          label: 'Auto Save',
          type: 'switch',
          description: 'Automatically save your chat history'
        },
        {
          key: 'language',
          label: 'Language',
          type: 'select',
          options: [
            { value: 'en', label: 'English' },
            { value: 'es', label: 'Spanish' },
            { value: 'fr', label: 'French' },
            { value: 'de', label: 'German' }
          ],
          description: 'Interface language'
        }
      ]
    }
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom color="primary" sx={{ fontWeight: 600 }}>
          Options & Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Customize your eLIMSChat.ai experience
        </Typography>
      </Box>

      {saved && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Settings saved successfully!
        </Alert>
      )}

      <Grid container spacing={3}>
        {settingSections.map((section, sectionIndex) => (
          <Grid item xs={12} md={6} lg={4} key={sectionIndex}>
            <Card elevation={2} sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  {section.icon}
                  <Typography variant="h6" sx={{ ml: 1, fontWeight: 600 }}>
                    {section.title}
                  </Typography>
                </Box>
                <Divider sx={{ mb: 2 }} />
                
                {section.settings.map((setting, settingIndex) => (
                  <Box key={setting.key} sx={{ mb: 2 }}>
                    {setting.type === 'switch' && (
                      <FormControlLabel
                        control={
                          <Switch
                            checked={setting.key === 'darkMode' ? isDarkMode : settings[setting.key]}
                            onChange={handleSettingChange(setting.key)}
                            color="primary"
                          />
                        }
                        label={setting.label}
                      />
                    )}
                    
                    {setting.type === 'select' && (
                      <FormControl fullWidth size="small">
                        <InputLabel>{setting.label}</InputLabel>
                        <Select
                          value={settings[setting.key]}
                          onChange={handleSettingChange(setting.key)}
                          label={setting.label}
                        >
                          {setting.options.map(option => (
                            <MenuItem key={option.value} value={option.value}>
                              {option.label}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    )}
                    
                    {setting.type === 'slider' && (
                      <Box>
                        <Typography variant="body2" gutterBottom>
                          {setting.label}: {settings[setting.key]}%
                        </Typography>
                        <Slider
                          value={settings[setting.key]}
                          onChange={handleSliderChange(setting.key)}
                          min={setting.min}
                          max={setting.max}
                          valueLabelDisplay="auto"
                          color="primary"
                        />
                      </Box>
                    )}
                    
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                      {setting.description}
                    </Typography>
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Button
          variant="contained"
          size="large"
          onClick={handleSave}
          startIcon={<StorageIcon />}
          sx={{ px: 4 }}
        >
          Save Settings
        </Button>
      </Box>
    </Container>
  );
}