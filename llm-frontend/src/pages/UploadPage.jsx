import { useRef, useState } from 'react';
import { Container, Typography, Paper, Box, Button, LinearProgress, List, ListItem, ListItemText, Alert } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { uploadFiles } from '../api';
import { useAuth } from '../context/AuthContext';

export default function UploadPage() {
  const { token } = useAuth();
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');
  const inputRef = useRef();

  const handleFileChange = (e) => {
    setSelectedFiles(Array.from(e.target.files));
    setResults([]);
    setError('');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setSelectedFiles(Array.from(e.dataTransfer.files));
    setResults([]);
    setError('');
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleUpload = async () => {
    if (!selectedFiles.length) return;
    setUploading(true);
    setError('');
    setResults([]);
    const formData = new FormData();
    selectedFiles.forEach(f => formData.append('files', f));
    try {
      const res = await uploadFiles(formData, token);
      setResults(res.data);
      setSelectedFiles([]);
    } catch (e) {
      setError(e.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 4, borderRadius: 4 }}>
        <Typography variant="h4" gutterBottom color="primary">
          Upload Documents
        </Typography>
        <Box
          sx={{ border: '2px dashed #90caf9', borderRadius: 2, p: 3, textAlign: 'center', mb: 2, bgcolor: '#f5fafd', cursor: 'pointer' }}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => inputRef.current.click()}
        >
          <CloudUploadIcon color="primary" sx={{ fontSize: 48, mb: 1 }} />
          <Typography variant="body1">Drag & drop files here, or click to select</Typography>
          <input
            type="file"
            multiple
            hidden
            ref={inputRef}
            onChange={handleFileChange}
          />
        </Box>
        {selectedFiles.length > 0 && (
          <List>
            {selectedFiles.map((file, i) => (
              <ListItem key={i}><ListItemText primary={file.name} /></ListItem>
            ))}
          </List>
        )}
        {uploading && <LinearProgress sx={{ my: 2 }} />}
        {error && <Alert severity="error" sx={{ my: 2 }}>{error}</Alert>}
        <Button
          variant="contained"
          color="primary"
          fullWidth
          sx={{ mt: 2, mb: 1 }}
          onClick={handleUpload}
          disabled={uploading || !selectedFiles.length}
        >
          Upload
        </Button>
        {results.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" color="secondary">Upload Results</Typography>
            <List>
              {results.map((r, i) => (
                <ListItem key={i}>
                  <ListItemText primary={r.file} secondary={`Chunks added: ${r.chunks_added}`} />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </Paper>
    </Container>
  );
}
