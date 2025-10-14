import React from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Card, 
  CardContent, 
  Grid, 
  Button, 
  Chip,
  Paper
} from '@mui/material';
import { 
  Chat as ChatIcon,
  Upload as UploadIcon,
  Analytics as AnalyticsIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  SmartToy as AIIcon
} from '@mui/icons-material';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function HomePage() {
  const { token, user } = useAuth();
  const features = [
    {
      icon: <ChatIcon color="primary" sx={{ fontSize: 40 }} />,
      title: "AI-Powered Chat",
      description: "Interact with advanced language models to get intelligent responses to your questions."
    },
    {
      icon: <UploadIcon color="primary" sx={{ fontSize: 40 }} />,
      title: "Document Upload",
      description: "Upload and process documents to build a knowledge base for the most up-to-date responses."
    },
    {
      icon: <AnalyticsIcon color="primary" sx={{ fontSize: 40 }} />,
      title: "Analytics & Feedback",
      description: "Track usage patterns and provide feedback to continuously improve the system."
    },
    {
      icon: <SecurityIcon color="primary" sx={{ fontSize: 40 }} />,
      title: "Secure & Private",
      description: "Eurofins data is protected with enterprise-grade security and privacy measures."
    },
    {
      icon: <SpeedIcon color="primary" sx={{ fontSize: 40 }} />,
      title: "Fast Processing",
      description: "Get quick responses with optimized algorithms and efficient data processing."
    },
    {
      icon: <AIIcon color="primary" sx={{ fontSize: 40 }} />,
      title: "Smart Indexing",
      description: "Advanced document indexing ensures relevant and contextual search results."
    }
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Hero Section */}
      <Box sx={{ textAlign: 'center', mb: 6 }}>
        {token && user && (
          <Typography 
            variant="h4" 
            component="div" 
            gutterBottom 
            sx={{ 
              fontWeight: 500,
              color: 'primary.main',
              mb: 2
            }}
          >
            Welcome back, {user.preferredName}!
          </Typography>
        )}
        <Typography 
          variant="h2" 
          component="h1" 
          gutterBottom 
          sx={{ 
            fontWeight: 700,
            background: 'linear-gradient(45deg, #1976d2 30%, #21CBF3 90%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          {token ? 'eLIMSChat.ai Dashboard' : 'Welcome to eLIMSChat.ai'}
        </Typography>
        <Typography 
          variant="h5" 
          color="text.secondary" 
          sx={{ mb: 4, fontWeight: 300 }}
        >
          A Proof of Concept for finding answers to all Eurofins LIMS products and workflows
        </Typography>
        <Box sx={{ mb: 4 }}>
          <Chip label="AI-Powered" color="primary" sx={{ mr: 1, mb: 1 }} />
          <Chip label="Document Processing" color="secondary" sx={{ mr: 1, mb: 1 }} />
          <Chip label="Enterprise Ready" variant="outlined" sx={{ mr: 1, mb: 1 }} />
        </Box>
        <Button 
          component={Link} 
          to={token ? "/ask" : "/login"}
          variant="contained" 
          size="large" 
          startIcon={<ChatIcon />}
          sx={{ 
            px: 4, 
            py: 1.5, 
            fontSize: '1.1rem',
            borderRadius: 3,
            boxShadow: 3
          }}
        >
          {token ? "Start Chatting" : "Login to Chat"}
        </Button>
      </Box>

      {/* About Section */}
      <Paper elevation={2} sx={{ p: 4, mb: 6, borderRadius: 3 }}>
        <Typography variant="h4" gutterBottom color="primary" sx={{ fontWeight: 600 }}>
          About This POC
        </Typography>
        <Typography variant="body1" paragraph color="text.secondary" sx={{ fontSize: '1.1rem', lineHeight: 1.7 }}>
          eLIMSChat.ai is a proof of concept that demonstrates the integration of Large Language Models (LLMs) 
          with Eurofins LIMS software product suites. This platform showcases how AI can enhance 
          laboratory workflows, improve data accessibility, and provide easy and quick answers to almost all eLIMS queries one might have.
        </Typography>
        <Typography variant="body1" paragraph color="text.secondary" sx={{ fontSize: '1.1rem', lineHeight: 1.7 }}>
          Built with modern web technologies including React, Material-UI, and Python backend, this system 
          demonstrates the potential for AI-driven solutions for improved understading and utlization of Eurofins LIMS products and workflows.
        </Typography>
        <Typography variant="body1" paragraph color="text.secondary" sx={{ fontSize: '1.1rem', lineHeight: 1.7 }}>
          This POC provides a configurable setup in the backend for choosing between various Embedding Models
          as well as LLM providers to identify the pros and cons of each and arrive at a combination that is tailored to the accuracy,
          performance and security requirements specified by each Program or ITAAG.
        </Typography>
      </Paper>

      {/* Features Grid */}
      <Typography variant="h4" gutterBottom align="center" color="primary" sx={{ mb: 4, fontWeight: 600 }}>
        Key Features
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mb: 6 }}>
        {/* Row 1 */}
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
          {features.slice(0, 2).map((feature, index) => (
            <Card 
              key={index}
              elevation={2} 
              sx={{ 
                width: { xs: '100%', md: '48%' },
                height: '250px',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                },
                borderRadius: 3
              }}
            >
              <CardContent sx={{ 
                p: 3, 
                textAlign: 'center', 
                height: '100%',
                display: 'flex', 
                flexDirection: 'column',
                justifyContent: 'space-between'
              }}>
                <Box>
                  <Box sx={{ mb: 2 }}>
                    {feature.icon}
                  </Box>
                  <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
                    {feature.title}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ 
                  lineHeight: 1.5,
                  textAlign: 'center',
                  wordWrap: 'break-word',
                  overflow: 'hidden'
                }}>
                  {feature.description}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
        
        {/* Row 2 */}
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
          {features.slice(2, 4).map((feature, index) => (
            <Card 
              key={index + 2}
              elevation={2} 
              sx={{ 
                width: { xs: '100%', md: '48%' },
                height: '250px',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                },
                borderRadius: 3
              }}
            >
              <CardContent sx={{ 
                p: 3, 
                textAlign: 'center', 
                height: '100%',
                display: 'flex', 
                flexDirection: 'column',
                justifyContent: 'space-between'
              }}>
                <Box>
                  <Box sx={{ mb: 2 }}>
                    {feature.icon}
                  </Box>
                  <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
                    {feature.title}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ 
                  lineHeight: 1.5,
                  textAlign: 'center',
                  wordWrap: 'break-word',
                  overflow: 'hidden'
                }}>
                  {feature.description}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
        
        {/* Row 3 */}
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
          {features.slice(4, 6).map((feature, index) => (
            <Card 
              key={index + 4}
              elevation={2} 
              sx={{ 
                width: { xs: '100%', md: '48%' },
                height: '250px',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                },
                borderRadius: 3
              }}
            >
              <CardContent sx={{ 
                p: 3, 
                textAlign: 'center', 
                height: '100%',
                display: 'flex', 
                flexDirection: 'column',
                justifyContent: 'space-between'
              }}>
                <Box>
                  <Box sx={{ mb: 2 }}>
                    {feature.icon}
                  </Box>
                  <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
                    {feature.title}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ 
                  lineHeight: 1.5,
                  textAlign: 'center',
                  wordWrap: 'break-word',
                  overflow: 'hidden'
                }}>
                  {feature.description}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
      </Box>

      {/* Call to Action */}
      <Paper 
        elevation={3} 
        sx={{ 
          p: 4, 
          textAlign: 'center',
          background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
          borderRadius: 3
        }}
      >
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
          Ready to Experience AI-Powered LIMS?
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3, fontSize: '1.1rem' }}>
          Explore the capabilities of eLIMSChat.ai and see how AI can transform laboratory workflows.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Button 
            component={Link} 
            to={token ? "/ask" : "/login"}
            variant="contained" 
            size="large"
            startIcon={<ChatIcon />}
            sx={{ borderRadius: 2 }}
          >
            {token ? "Try the Chat" : "Login to Chat"}
          </Button>
          <Button 
            component={Link} 
            to="/health" 
            variant="outlined" 
            size="large"
            sx={{ borderRadius: 2 }}
          >
            System Health
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}
