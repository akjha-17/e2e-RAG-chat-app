import React, { useEffect, useState } from 'react';
import { 
  Container, 
  Typography, 
  Paper, 
  CircularProgress, 
  Box, 
  Alert,
  Card,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Divider,
  Button
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  RadioButtonUnchecked as UncheckedIcon,
  Computer as ComputerIcon,
  Cloud as CloudIcon,
  Memory as MemoryIcon,
  SmartToy as AIIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { getHealth } from '../api';

export default function HealthPage() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const checkHealth = () => {
    setLoading(true);
    setError('');
    getHealth()
      .then(res => {
        setHealth(res.data);
        setLoading(false);
      })
      .catch(e => {
        setError('Could not reach backend');
        setLoading(false);
      });
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const llmBackends = [
    { name: 'OpenAI', value: 'openai', icon: <CloudIcon /> },
    { name: 'Huggingface', value: 'hf', icon: <AIIcon /> },
    { name: 'Ollama', value: 'ollama', icon: <ComputerIcon /> }
  ];

  const embeddingBackends = [
    { name: 'OpenAI', value: 'openai', icon: <CloudIcon /> },
    { name: 'Huggingface', value: 'hf', icon: <AIIcon /> }
  ];

  const renderBackendList = (backends, currentBackend, title, hasError = false) => {
    const isBackendActive = !hasError && currentBackend;
    
    return (
      <Card elevation={2} sx={{ height: '100%' }}>
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            {isBackendActive ? (
              <CheckCircleIcon sx={{ color: 'success.main', fontSize: 24, mr: 1.5 }} />
            ) : (
              <ErrorIcon sx={{ color: 'error.main', fontSize: 24, mr: 1.5 }} />
            )}
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {title}
            </Typography>
          </Box>
          <Divider sx={{ mb: 2 }} />
          <List dense sx={{ py: 0 }}>
            {backends.map((backend, index) => {
              const isSelected = !hasError && backend.value === currentBackend;
              return (
                <ListItem 
                  key={backend.value}
                  sx={{ 
                    px: 0,
                    py: 1,
                    borderRadius: 2,
                    mb: index < backends.length - 1 ? 1 : 0,
                    '&:hover': {
                      backgroundColor: 'grey.50'
                    }
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 40 }}>
                    {React.cloneElement(backend.icon, { 
                      sx: { 
                        color: 'grey.600',
                        fontSize: 20 
                      } 
                    })}
                  </ListItemIcon>
                  <ListItemText 
                    primary={backend.name}
                    primaryTypographyProps={{
                      variant: 'body1',
                      fontWeight: 400,
                      color: 'text.primary'
                    }}
                  />
                  <Chip 
                    label={isSelected ? "Active" : "Inactive"} 
                    size="small" 
                    color={isSelected ? "success" : "default"} 
                    variant="outlined"
                    sx={{ ml: 1 }}
                  />
                </ListItem>
              );
            })}
          </List>
        </CardContent>
      </Card>
    );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, textAlign: 'left' }}>
          System Health
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            Monitor backend services and configuration status
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={checkHealth}
            disabled={loading}
            sx={{ 
              textTransform: 'none',
              fontWeight: 500
            }}
          >
            Check Health
          </Button>
        </Box>
      </Box>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress size={40} />
        </Box>
      )}
      
      {!loading && error ? (
        <Box>
          {/* Error Status Card */}
          <Card elevation={3} sx={{ mb: 4, borderRadius: 3 }}>
            <CardContent sx={{ p: 4, textAlign: 'center' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
                <ErrorIcon sx={{ color: 'error.main', fontSize: 40, mr: 2 }} />
                <Typography variant="h5" sx={{ fontWeight: 600, color: 'error.main' }}>
                  Error
                </Typography>
              </Box>
              <Typography variant="body1" color="text.secondary">
                Could not reach backend services
              </Typography>
            </CardContent>
          </Card>

          {/* Backend Configuration - Error State */}
          <Box sx={{ display: 'flex', gap: 3, width: '100%' }}>
            <Box sx={{ flex: 1 }}>
              {renderBackendList(embeddingBackends, null, 'Embedding Backend', true)}
            </Box>
            <Box sx={{ flex: 1 }}>
              {renderBackendList(llmBackends, null, 'LLM Backend', true)}
            </Box>
          </Box>
        </Box>
      ) : !loading && health ? (
        <Box>
          {/* Overall Status Card */}
          <Card elevation={3} sx={{ mb: 4, borderRadius: 3 }}>
            <CardContent sx={{ p: 4, textAlign: 'center' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
                <CheckCircleIcon sx={{ color: 'success.main', fontSize: 40, mr: 2 }} />
                <Typography variant="h5" sx={{ fontWeight: 600, color: 'success.main' }}>
                  All OK
                </Typography>
              </Box>
              <Typography variant="body1" color="text.secondary">
                All backend services are operational
              </Typography>
            </CardContent>
          </Card>

          {/* Backend Configuration */}
          <Box sx={{ display: 'flex', gap: 3, width: '100%' }}>
            <Box sx={{ flex: 1 }}>
              {renderBackendList(embeddingBackends, health.embedding, 'Embedding Backend', false)}
            </Box>
            <Box sx={{ flex: 1 }}>
              {renderBackendList(llmBackends, health.llm_backend, 'LLM Backend', false)}
            </Box>
          </Box>
        </Box>
      ) : null}
    </Container>
  );
}
