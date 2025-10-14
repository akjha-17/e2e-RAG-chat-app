import { useState } from 'react';
import { Container, Typography, Paper, Box, Button, TextField, LinearProgress, Alert } from '@mui/material';
import { reindex } from '../api';
import { useAuth } from '../context/AuthContext';

export default function ReindexPage() {
  const { token } = useAuth();
  const [folder, setFolder] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleReindex = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await reindex(folder, token);
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Reindex failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 4, borderRadius: 4 }}>
        <Typography variant="h4" gutterBottom color="primary">
          Reindex Documents
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <TextField
            fullWidth
            label="Folder (optional)"
            value={folder}
            onChange={e => setFolder(e.target.value)}
            disabled={loading}
          />
          <Button variant="contained" color="primary" onClick={handleReindex} disabled={loading}>
            Reindex
          </Button>
        </Box>
        {loading && <LinearProgress sx={{ my: 2 }} />}
        {error && <Alert severity="error" sx={{ my: 2 }}>{error}</Alert>}
        {result && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body1">Folder: <b>{result.folder}</b></Typography>
            <Typography variant="body2">Chunks indexed: {result.chunks_indexed}</Typography>
          </Box>
        )}
      </Paper>
    </Container>
  );
}
