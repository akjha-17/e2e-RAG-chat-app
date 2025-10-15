import { useState, useEffect, useRef } from 'react';
import { 
  askQuestion, 
  getChatSessions, 
  createChatSession, 
  getChatSessionDetail,
  deleteChatSession,
  updateChatSession,
  submitMessageFeedback
} from '../api';
import { useAuth } from '../context/AuthContext';
import { 
  Container, 
  Paper, 
  Typography, 
  Box, 
  TextField, 
  Button, 
  CircularProgress, 
  List, 
  ListItem, 
  ListItemText, 
  Divider, 
  Rating, 
  Alert, 
  LinearProgress,
  Card,
  CardContent,
  Chip,
  Collapse,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  ListItemButton,
  Grid,
  Drawer,
  useMediaQuery,
  useTheme,
  Fab,
  Badge,
  Tooltip,
  Menu,
  MenuItem
} from '@mui/material';
import { 
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as AIIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Chat as ChatIcon,
  Menu as MenuIcon,
  History as HistoryIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  MoreVert as MoreVertIcon
} from '@mui/icons-material';
import { useSidebar } from '../context/SidebarContext';
import { useSettings } from '../context/SettingsContext';

export default function ChatWithAIPage() {
  const { token, user } = useAuth();
  const { mainSidebarOpen } = useSidebar();
  const { settings } = useSettings();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const messagesEndRef = useRef(null);

  // Main states
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Chat session states
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sessionLoading, setSessionLoading] = useState(false);

  // UI states
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);
  const [expandedSources, setExpandedSources] = useState(new Set());
  const [feedbackStates, setFeedbackStates] = useState({}); // Track feedback per message

  // Scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load chat sessions on mount
  useEffect(() => {
    loadChatSessions();
  }, []);

  const loadChatSessions = async () => {
    try {
      const res = await getChatSessions(token);
      setSessions(res.data);
      
      // If no current session and sessions exist, select the first one
      if (!currentSession && res.data.length > 0) {
        selectSession(res.data[0]);
      }
    } catch (e) {
      console.error('Failed to load sessions:', e);
    }
  };

  const selectSession = async (session) => {
    setCurrentSession(session);
    setSessionLoading(true);
    try {
      const res = await getChatSessionDetail(session.id, token);
      setMessages(res.data.messages);
    } catch (e) {
      setError('Failed to load chat history');
    } finally {
      setSessionLoading(false);
    }
  };

  const startNewChat = () => {
    // Simply clear current session - new session will be auto-created when user sends first message
    setCurrentSession(null);
    setMessages([]);
    setError('');
  };

  const deleteSession = async (sessionId) => {
    try {
      console.log('Attempting to delete session:', sessionId);
      console.log('Current sessions before delete:', sessions.length);
      
      const response = await deleteChatSession(sessionId, token);
      console.log('Delete response:', response);
      
      // If deleted session was current, clear it first
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
      
      // Option 1: Filter out the deleted session locally (faster)
      setSessions(prevSessions => {
        const filtered = prevSessions.filter(s => s.id !== sessionId);
        console.log('Sessions after local filter:', filtered.length);
        return filtered;
      });
      
      // Option 2: Also refresh from server as backup (commented out to prevent the "all deleted" issue)
      // setTimeout(async () => {
      //   try {
      //     const sessionsResponse = await getChatSessions(token);
      //     setSessions(sessionsResponse.data.sessions || []);
      //   } catch (refreshError) {
      //     console.error('Failed to refresh sessions:', refreshError);
      //   }
      // }, 500);
      
      console.log('Session deleted successfully');
      setError(''); // Clear any existing errors
    } catch (e) {
      console.error('Delete session error:', e);
      console.error('Error response:', e.response?.data);
      console.error('Error status:', e.response?.status);
      setError(`Failed to delete session: ${e.response?.data?.detail || e.message}`);
    }
  };

  const toggleSourceExpanded = (messageIndex, sourceIndex) => {
    const key = `${messageIndex}-${sourceIndex}`;
    const newExpanded = new Set(expandedSources);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedSources(newExpanded);
  };

  const handleAsk = async () => {
    if (!query.trim()) return;
    
    const currentQuery = query;
    setQuery('');
    setError('');
    
    let sessionToUse = currentSession;
    
    // Create session if none exists
    if (!sessionToUse) {
      try {
        // Generate a smart title from the user's query
        const generateSessionTitle = (text) => {
          // Remove common question words and clean up
          const cleanText = text
            .replace(/^(what|how|why|when|where|who|which|can you|could you|please|help me)\s+/i, '')
            .replace(/\?+$/, '')
            .trim();
          
          // Take first 40 characters and ensure it doesn't cut off mid-word
          let title = cleanText.slice(0, 40);
          if (cleanText.length > 40) {
            const lastSpace = title.lastIndexOf(' ');
            if (lastSpace > 20) { // Ensure we have at least 20 chars
              title = title.slice(0, lastSpace);
            }
            title += '...';
          }
          
          // Capitalize first letter
          return title.charAt(0).toUpperCase() + title.slice(1);
        };
        
        const res = await createChatSession({ 
          title: generateSessionTitle(currentQuery) 
        }, token);
        const newSession = res.data;
        setSessions(prev => [newSession, ...prev]);
        setCurrentSession(newSession);
        sessionToUse = newSession; // Use the newly created session immediately
      } catch (e) {
        setError('Failed to create chat session');
        setQuery(currentQuery); // Restore query on error
        return;
      }
    }
    
    // Add user message immediately
    const userMessage = {
      id: Date.now(),
      message_type: 'user',
      content: currentQuery,
      timestamp: new Date().toISOString(),
      sources: []
    };
    
    // Add loading assistant message
    const loadingMessage = {
      id: Date.now() + 1,
      message_type: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      sources: [],
      loading: true
    };
    
    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setLoading(true);
    
    try {
      const res = await askQuestion({ 
        query: currentQuery,
        session_id: sessionToUse.id, // Use the guaranteed session
        response_length: settings.responseLength // Add response length setting
      }, token);
      
      const assistantMessage = {
        id: Date.now() + 2,
        message_type: 'assistant',
        content: res.data.answer,
        sources: res.data.sources,
        timestamp: new Date().toISOString(),
        rating: null,
        feedback_comment: ''
      };
      
      // Replace loading message with actual response
      setMessages(prev => [
        ...prev.slice(0, -1), // Remove loading message
        assistantMessage
      ]);
      
      // Refresh sessions to update message count
      loadChatSessions();
      
    } catch (e) {
      setError(e.response?.data?.detail || 'Error getting answer');
      setQuery(currentQuery); // Restore query on error
      // Remove loading message
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const handleMessageFeedback = async (messageId, rating, comment = '') => {
    try {
      await submitMessageFeedback({ 
        message_id: messageId, 
        rating, 
        comment 
      }, token);
      
      // Update local state
      setMessages(prev => prev.map(msg => 
        msg.id === messageId ? { ...msg, rating, feedback_comment: comment } : msg
      ));
      
      // Update feedback state
      setFeedbackStates(prev => ({
        ...prev,
        [messageId]: { rating, comment, submitted: true }
      }));
    } catch (e) {
      console.error('Feedback failed:', e);
    }
  };

  const renderMessage = (message, index) => {
    const isUser = message.message_type === 'user';
    const isLoading = message.loading;

    return (
      <Box
        key={message.id}
        sx={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          mb: 2,
          mx: 2
        }}
      >
        <Box
          sx={{
            maxWidth: '85%',
            minWidth: '20%'
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 1,
              flexDirection: isUser ? 'row-reverse' : 'row'
            }}
          >
            <Box
              sx={{
                width: 40,
                height: 40,
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                bgcolor: isUser ? 'primary.main' : 'success.main',
                color: 'white',
                flexShrink: 0,
                mt: 0.5
              }}
            >
              {isUser ? <PersonIcon /> : <AIIcon />}
            </Box>
            
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Paper
                elevation={2}
                sx={{
                  p: 2,
                  bgcolor: isUser ? 'primary.main' : 'grey.100',
                  color: isUser ? 'white' : 'text.primary',
                  borderRadius: 3,
                  borderTopLeftRadius: isUser ? 3 : 1,
                  borderTopRightRadius: isUser ? 1 : 3,
                  wordWrap: 'break-word'
                }}
              >
                {isLoading ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={16} sx={{ color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                      AI is thinking...
                    </Typography>
                  </Box>
                ) : (
                  <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                    {message.content}
                  </Typography>
                )}
              </Paper>
              
              {/* Sources for AI messages - only show if setting is enabled */}
              {!isUser && !isLoading && message.sources && message.sources.length > 0 && settings.showSources && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                    📚 Sources ({message.sources.length}):
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {message.sources.map((src, i) => (
                      <Box key={i} sx={{ border: '1px solid #e0e0e0', borderRadius: 1, bgcolor: 'white' }}>
                        <Box 
                          sx={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            justifyContent: 'space-between',
                            p: 1,
                            cursor: 'pointer',
                            '&:hover': { backgroundColor: '#f5f5f5' },
                            minWidth: 0 // Allow flexbox shrinking
                          }}
                          onClick={() => toggleSourceExpanded(index, i)}
                        >
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0, flex: 1 }}>
                            <Chip 
                              label={`${(src.file && (src.file.split('/').pop() || src.file.split('\\').pop() || src.file)) || 'unknown'}${(src.page_number ?? -1) !== -1 ? ` - Page ${src.page_number}` : ''}`}
                              variant="outlined"
                              size="small"
                              sx={{ 
                                fontSize: '0.7rem', 
                                height: 20,
                                '& .MuiChip-label': {
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap'
                                }
                              }}
                            />
                            <Typography variant="caption" color="text.secondary">
                              {Math.round(((src.score_normalized ?? src.score ?? 0) * 100))}%
                            </Typography>
                          </Box>
                          <IconButton size="small" sx={{ flexShrink: 0 }}>
                            {expandedSources.has(`${index}-${i}`) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                          </IconButton>
                        </Box>
                        <Collapse in={expandedSources.has(`${index}-${i}`)}>
                          <Box sx={{ p: 1.5, backgroundColor: '#fafafa', borderTop: '1px solid #e0e0e0' }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                              <Typography variant="caption" color="text.secondary">
                                Chunk {src.chunk_id ?? src.chunkId ?? 'n/a'}
                              </Typography>
                              <Typography 
                                variant="caption" 
                                color="text.secondary"
                                sx={{ 
                                  fontSize: '0.65rem',
                                  maxWidth: '200px',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap'
                                }}
                                title={src.file} // Show full path on hover
                              >
                                {src.file.split('/').pop() || src.file.split('\\').pop() || src.file}
                              </Typography>
                            </Box>
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                mt: 0.5, 
                                fontSize: '0.8rem', 
                                lineHeight: 1.4,
                                maxHeight: '200px',
                                overflow: 'auto',
                                wordBreak: 'break-word'
                              }}
                            >
                              {src.preview || src.text || src.snippet || ''}
                            </Typography>
                          </Box>
                        </Collapse>
                      </Box>
                    ))}
                  </Box>
                </Box>
              )}
              
              {/* Feedback for AI messages - only show if setting is enabled */}
              {!isUser && !isLoading && message.content && settings.enableFeedback && (
                <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Tooltip title="Helpful response">
                    <IconButton
                      size="small"
                      onClick={() => handleMessageFeedback(message.id, 4)} // Map thumbs up to 4 stars (good rating)
                      disabled={feedbackStates[message.id]?.submitted}
                      sx={{ 
                        color: feedbackStates[message.id]?.rating >= 4 ? 'success.main' : 'action.disabled',
                        '&:hover': { bgcolor: 'success.50' }
                      }}
                    >
                      <ThumbUpIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Not helpful">
                    <IconButton
                      size="small"
                      onClick={() => handleMessageFeedback(message.id, 2)} // Map thumbs down to 2 stars (poor rating)
                      disabled={feedbackStates[message.id]?.submitted}
                      sx={{ 
                        color: feedbackStates[message.id]?.rating <= 2 ? 'error.main' : 'action.disabled',
                        '&:hover': { bgcolor: 'error.50' }
                      }}
                    >
                      <ThumbDownIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  {feedbackStates[message.id]?.submitted && (
                    <Typography variant="caption" color="success.main">
                      Thanks for your feedback!
                    </Typography>
                  )}
                </Box>
              )}
              
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                {new Date(message.timestamp).toLocaleTimeString()}
              </Typography>
            </Box>
          </Box>
        </Box>
      </Box>
    );
  };

  return (
    <Box sx={{ 
      position: 'fixed', 
      top: 64, 
      left: 0, 
      right: 0, 
      bottom: 0, 
      display: 'flex', 
      height: 'calc(100vh - 64px)', 
      width: '100vw',
      zIndex: 1
    }}>
      {/* Chat Sessions Sidebar - positioned to extend from main sidebar or go to left when main sidebar is closed */}
      <Drawer
        variant={isMobile ? "temporary" : "persistent"}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        sx={{
          width: 300,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: 300,
            boxSizing: 'border-box',
            borderRight: '1px solid #e0e0e0',
            borderLeft: mainSidebarOpen && !isMobile ? '1px solid #e0e0e0' : 'none',
            zIndex: (theme) => isMobile ? theme.zIndex.drawer + 2 : theme.zIndex.drawer + 2,
            position: 'fixed',
            height: 'calc(100vh - 64px)',
            top: 64,
            left: isMobile ? 0 : (mainSidebarOpen ? 240 : 0), // Move to left edge when main sidebar is closed
            transition: 'left 0.3s ease'
          },
        }}
      >
        <Box sx={{ p: 3, borderBottom: '1px solid #e0e0e0', pt: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, color: 'primary.main', mb: 3 }}>
            Chat Sessions
          </Typography>
          <Button
            fullWidth
            variant="contained"
            startIcon={<AddIcon />}
            onClick={startNewChat}
            sx={{ 
              borderRadius: 2, 
              py: 1.5,
              boxShadow: 2,
              '&:hover': {
                boxShadow: 3
              }
            }}
          >
            New Chat
          </Button>
        </Box>
        
        <List sx={{ flex: 1, overflow: 'auto' }}>
          {sessions.map((session) => (
            <ListItemButton
              key={session.id}
              selected={currentSession?.id === session.id}
              onClick={() => selectSession(session)}
              sx={{
                mx: 1,
                my: 0.5,
                borderRadius: 2,
                '&.Mui-selected': {
                  bgcolor: 'primary.50',
                  '&:hover': {
                    bgcolor: 'primary.100',
                  }
                }
              }}
            >
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: currentSession?.id === session.id ? 600 : 400,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}
                >
                  {session.title}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                  <Typography variant="caption" color="text.secondary">
                    {session.message_count} messages
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    •
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(session.updated_at).toLocaleDateString()}
                  </Typography>
                </Box>
              </Box>
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  if (window.confirm('Are you sure you want to delete this chat session?')) {
                    deleteSession(session.id);
                  }
                }}
                sx={{ 
                  ml: 1,
                  color: 'error.main',
                  '&:hover': {
                    backgroundColor: 'error.light',
                    color: 'error.contrastText'
                  }
                }}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </ListItemButton>
          ))}
        </List>
      </Drawer>

      {/* Main Chat Area - positioned to work with both sidebars */}
      <Box sx={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column', 
        minHeight: 'calc(100vh - 64px)',
        ml: sidebarOpen && !isMobile ? '300px' : 0, // Offset by chat sidebar when it's open
        position: 'relative'
      }}>
        {/* Header */}
        <Box
          sx={{
            p: 2,
            borderBottom: '1px solid #e0e0e0',
            bgcolor: 'background.paper',
            display: 'flex',
            alignItems: 'center',
            gap: 2
          }}
        >
          {isMobile && (
            <IconButton onClick={() => setSidebarOpen(true)}>
              <MenuIcon />
            </IconButton>
          )}
          <ChatIcon sx={{ color: 'primary.main' }} />
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {currentSession?.title || 'Chat with AI'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Intelligent conversations powered by RAG
            </Typography>
          </Box>
          {user && (
            <Chip
              label={user.preferred_name || user.username}
              variant="outlined"
              sx={{ fontWeight: 500 }}
            />
          )}
        </Box>

        {/* Messages Area */}
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            bgcolor: '#fafafa',
            display: 'flex',
            flexDirection: 'column',
            pb: '100px' // Add padding bottom for sticky input
          }}
        >
          {sessionLoading ? (
            <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CircularProgress />
            </Box>
          ) : messages.length === 0 ? (
            <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center', p: 4 }}>
              <Box>
                <AIIcon sx={{ fontSize: 80, color: 'primary.main', mb: 2 }} />
                <Typography variant="h5" color="primary" sx={{ fontWeight: 600, mb: 2 }}>
                  Welcome to ElimsChat AI
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 400 }}>
                  Start a conversation by typing your question below. I'll search through your knowledge base and provide intelligent responses.
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
                  <Chip
                    label="What can you help me with?"
                    variant="outlined"
                    onClick={() => setQuery("What can you help me with?")}
                    clickable
                  />
                  <Chip
                    label="Tell me about the documents"
                    variant="outlined"
                    onClick={() => setQuery("Tell me about the documents in your knowledge base")}
                    clickable
                  />
                </Box>
              </Box>
            </Box>
          ) : (
            <Box sx={{ p: 2, pb: 4 }}>
              {messages.map((message, index) => renderMessage(message, index))}
              <div ref={messagesEndRef} />
            </Box>
          )}
        </Box>

        {/* Input Area */}
        <Box
          sx={{
            position: 'fixed',
            bottom: 0,
            left: isMobile ? 0 : (sidebarOpen ? (mainSidebarOpen ? '540px' : '300px') : (mainSidebarOpen ? '240px' : '0px')),
            right: 0,
            p: 2,
            borderTop: '1px solid #e0e0e0',
            bgcolor: 'background.paper',
            zIndex: 1000,
            boxShadow: '0 -2px 8px rgba(0,0,0,0.1)',
            transition: 'left 0.3s ease'
          }}
        >
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end' }}>
            <TextField
              fullWidth
              placeholder="Type your message..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleAsk();
                }
              }}
              disabled={loading}
              multiline
              maxRows={4}
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 3,
                  bgcolor: 'background.default'
                }
              }}
            />
            <Button
              variant="contained"
              onClick={handleAsk}
              disabled={loading || !query.trim()}
              sx={{
                minWidth: 60,
                height: 56,
                borderRadius: 3,
                px: 3
              }}
            >
              {loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
            </Button>
          </Box>
        </Box>
      </Box>



      {/* Mobile FAB */}
      {isMobile && !sidebarOpen && (
        <Fab
          color="primary"
          sx={{ position: 'fixed', bottom: 80, right: 16 }}
          onClick={() => setSidebarOpen(true)}
        >
          <HistoryIcon />
        </Fab>
      )}
    </Box>
  );
}