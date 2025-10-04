import React, { useState } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  TextField,
  Button,
  Tabs,
  Tab,
  Box,
  Alert
} from '@mui/material';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import CameraAltIcon from '@mui/icons-material/CameraAlt';
import WebcamScanner from '../components/WebcamScanner';
import VerificationResult from '../components/VerificationResult';
import { verifyICText, verifyICImage } from '../services/api';

const ScannerPage = () => {
  const [tabValue, setTabValue] = useState(0);
  const [markingText, setMarkingText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setResult(null);
    setError(null);
  };

  const handleTextVerify = async () => {
    if (!markingText.trim()) {
      setError('Please enter IC marking text');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await verifyICText(markingText);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.error || 'Verification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleImageCapture = async (imageSrc) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await verifyICImage(imageSrc);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.error || 'Verification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        IC Verification Scanner
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Verify integrated chips by scanning the OEM marking or entering the text manually
      </Typography>

      <Paper sx={{ mt: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} variant="fullWidth">
          <Tab icon={<CameraAltIcon />} label="Camera Scan" />
          <Tab icon={<TextFieldsIcon />} label="Manual Entry" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {tabValue === 0 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <WebcamScanner onCapture={handleImageCapture} loading={loading} />
              </Grid>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 3, backgroundColor: '#f5f5f5' }}>
                  <Typography variant="h6" gutterBottom>
                    Instructions
                  </Typography>
                  <Typography variant="body2" paragraph>
                    1. Position your camera to clearly capture the IC chip marking
                  </Typography>
                  <Typography variant="body2" paragraph>
                    2. Ensure good lighting for best OCR results
                  </Typography>
                  <Typography variant="body2" paragraph>
                    3. Click "Capture & Verify" to scan the chip
                  </Typography>
                  <Typography variant="body2" paragraph>
                    4. The system will extract text using OCR and verify against the OEM database
                  </Typography>
                  <Alert severity="info" sx={{ mt: 2 }}>
                    <strong>Tip:</strong> Use the rear camera on mobile devices for better focus
                  </Alert>
                </Paper>
              </Grid>
            </Grid>
          )}

          {tabValue === 1 && (
            <Box>
              <TextField
                fullWidth
                label="IC Marking Text"
                placeholder="e.g., ATmega328P, STM32F103C8T6, NE555P"
                value={markingText}
                onChange={(e) => setMarkingText(e.target.value)}
                variant="outlined"
                sx={{ mb: 2 }}
                helperText="Enter the text marking visible on the IC chip"
              />
              <Button
                variant="contained"
                color="primary"
                size="large"
                onClick={handleTextVerify}
                disabled={loading || !markingText.trim()}
                fullWidth
              >
                {loading ? 'Verifying...' : 'Verify IC'}
              </Button>

              <Paper sx={{ p: 3, backgroundColor: '#f5f5f5', mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  How to use Manual Entry
                </Typography>
                <Typography variant="body2" paragraph>
                  Enter the exact text marking visible on the IC chip. This can include:
                </Typography>
                <ul style={{ marginTop: 0 }}>
                  <li><Typography variant="body2">Model number (e.g., ATmega328P)</Typography></li>
                  <li><Typography variant="body2">Manufacturer code (e.g., TI, STM)</Typography></li>
                  <li><Typography variant="body2">Additional markings on the chip surface</Typography></li>
                </ul>
                <Alert severity="warning" sx={{ mt: 2 }}>
                  Case-insensitive matching is performed. Spaces and special characters are normalized.
                </Alert>
              </Paper>
            </Box>
          )}
        </Box>
      </Paper>

      {result && <VerificationResult result={result} />}
    </Container>
  );
};

export default ScannerPage;
