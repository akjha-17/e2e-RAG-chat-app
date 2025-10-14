import { useState } from 'react';
import { Container, Typography, Paper, Box, TextField, Button, Rating, Alert, LinearProgress, Chip } from '@mui/material';
import { sendFeedback } from '../api';
import { useAuth } from '../context/AuthContext';

export default function FeedbackPage() {
  const { token, user } = useAuth();
  const [query, setQuery] = useState('');
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    setSuccess(false);
    try {
      // Use user's preferred name or username as session identifier for general feedback
      const userSessionId = `general_feedback_${user?.id || user?.username || 'anonymous'}`;
      await sendFeedback({ session_id: userSessionId, query, rating, comment }, token);
      setSuccess(true);
      setQuery('');
      setRating(0);
      setComment('');
    } catch (e) {
      setError(e.response?.data?.detail || 'Feedback failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 4, borderRadius: 4 }}>
        <Typography variant="h4" gutterBottom color="primary">
          General Feedback
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Share your overall experience with the AI system. Your feedback helps us improve!
        </Typography>
        
        {user && (
          <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Feedback from:
            </Typography>
            <Chip 
              label={user.preferred_name || user.username} 
              size="small" 
              variant="outlined" 
              color="primary"
            />
          </Box>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField 
            label="What would you like to provide feedback about?" 
            value={query} 
            onChange={e => setQuery(e.target.value)} 
            disabled={loading} 
            placeholder="e.g., Overall system performance, AI response quality, user interface..."
            multiline
            minRows={2}
          />
          <Box>
            <Typography component="legend" variant="body2" sx={{ mb: 1 }}>
              Overall Rating *
            </Typography>
            <Rating value={rating} onChange={(_, v) => setRating(v)} disabled={loading} size="large" />
          </Box>
          <TextField 
            label="Additional Comments" 
            value={comment} 
            onChange={e => setComment(e.target.value)} 
            multiline 
            minRows={3} 
            disabled={loading} 
            placeholder="Please share any specific suggestions or details about your experience..."
          />
          {loading && <LinearProgress />}
          {error && <Alert severity="error">{error}</Alert>}
          {success && <Alert severity="success">Thank you for your feedback! We appreciate your input.</Alert>}
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleSubmit} 
            disabled={loading || !query || !rating}
            size="large"
          >
            Submit Feedback
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}
