import React, { useState, useRef } from 'react';
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
  Alert,
  Chip,
  Stack,
  Divider,
  ButtonGroup
} from '@mui/material';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import CameraAltIcon from '@mui/icons-material/CameraAlt';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import WebcamScanner from '../components/WebcamScanner';
import VerificationResult from '../components/VerificationResult';
import { verifyICText, verifyICImage } from '../services/api';

const ScannerPage = () => {
  const [tabValue, setTabValue] = useState(0);
  const [markingText, setMarkingText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [uploadedImage, setUploadedImage] = useState(null);
  const fileInputRef = useRef(null);

  // Test data for manual testing
  const testICData = [
    { name: 'STM32F103C8T6', description: 'STMicroelectronics MCU' },
    { name: 'ATmega328P', description: 'Microchip AVR MCU' },
    { name: 'NE555P', description: 'Texas Instruments Timer' },
    { name: 'LM358N TI', description: 'Texas Instruments Op-Amp' },
    { name: 'ESP32-WROOM-32', description: 'Espressif WiFi Module' },
    { name: 'PIC16F877A', description: 'Microchip PIC MCU' },
    { name: 'FAKE12345XYZ', description: 'Test Fake IC (should fail)' }
  ];

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

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setUploadedImage(e.target.result);
        setError(null);
      };
      reader.readAsDataURL(file);
    } else {
      setError('Please select a valid image file');
    }
  };

  const handleUploadedImageVerify = async () => {
    if (!uploadedImage) {
      setError('Please upload an image first');
      return;
    }
    await handleImageCapture(uploadedImage);
  };

  const handleTestDataClick = (testIC) => {
    setMarkingText(testIC.name);
    setError(null);
    setResult(null);
  };

  const handleQuickTest = async (testIC) => {
    setMarkingText(testIC.name);
    setError(null);
    setResult(null);
    setLoading(true);

    try {
      const data = await verifyICText(testIC.name);
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
          <Tab icon={<UploadFileIcon />} label="Upload Image" />
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
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Box sx={{ textAlign: 'center', p: 4, border: '2px dashed #ccc', borderRadius: 2 }}>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    style={{ display: 'none' }}
                    ref={fileInputRef}
                  />
                  
                  {!uploadedImage ? (
                    <Box>
                      <UploadFileIcon sx={{ fontSize: 64, color: '#ccc', mb: 2 }} />
                      <Typography variant="h6" gutterBottom>
                        Upload IC Image
                      </Typography>
                      <Typography variant="body2" color="text.secondary" paragraph>
                        Select an image file of an IC chip for verification
                      </Typography>
                      <Button
                        variant="contained"
                        onClick={() => fileInputRef.current?.click()}
                        startIcon={<UploadFileIcon />}
                      >
                        Choose Image
                      </Button>
                    </Box>
                  ) : (
                    <Box>
                      <img
                        src={uploadedImage}
                        alt="Uploaded IC"
                        style={{
                          maxWidth: '100%',
                          maxHeight: '300px',
                          objectFit: 'contain',
                          borderRadius: '8px',
                          marginBottom: '16px'
                        }}
                      />
                      <Box>
                        <Button
                          variant="contained"
                          color="primary"
                          onClick={handleUploadedImageVerify}
                          disabled={loading}
                          sx={{ mr: 2 }}
                        >
                          {loading ? 'Verifying...' : 'Verify Image'}
                        </Button>
                        <Button
                          variant="outlined"
                          onClick={() => {
                            setUploadedImage(null);
                            fileInputRef.current.value = '';
                          }}
                          disabled={loading}
                        >
                          Choose Different Image
                        </Button>
                      </Box>
                    </Box>
                  )}
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 3, backgroundColor: '#f5f5f5' }}>
                  <Typography variant="h6" gutterBottom>
                    Upload Instructions
                  </Typography>
                  <Typography variant="body2" paragraph>
                    • Supported formats: JPG, PNG, BMP, TIFF
                  </Typography>
                  <Typography variant="body2" paragraph>
                    • Ensure the IC marking is clearly visible
                  </Typography>
                  <Typography variant="body2" paragraph>
                    • Good lighting and focus improve accuracy
                  </Typography>
                  <Typography variant="body2" paragraph>
                    • The system will extract text using OCR
                  </Typography>
                  <Alert severity="info" sx={{ mt: 2 }}>
                    <strong>Tip:</strong> Use macro lens or close-up shots for better text extraction
                  </Alert>
                </Paper>
              </Grid>
            </Grid>
          )}

          {tabValue === 2 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
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
                    sx={{ mb: 3 }}
                  >
                    {loading ? 'Verifying...' : 'Verify IC'}
                  </Button>

                  <Divider sx={{ mb: 3 }}>
                    <Typography variant="body2" color="text.secondary">
                      Or try test data
                    </Typography>
                  </Divider>

                  <Typography variant="h6" gutterBottom>
                    Quick Test Data
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Click any chip below to test the verification system:
                  </Typography>
                  
                  <Stack spacing={1}>
                    {testICData.map((testIC, index) => (
                      <Box key={index} sx={{ display: 'flex', gap: 1 }}>
                        <Chip
                          label={testIC.name}
                          onClick={() => handleTestDataClick(testIC)}
                          clickable
                          variant={markingText === testIC.name ? "filled" : "outlined"}
                          color={testIC.name.includes('FAKE') ? "error" : "primary"}
                          sx={{ flexGrow: 1, justifyContent: 'flex-start' }}
                        />
                        <Button
                          size="small"
                          variant="contained"
                          onClick={() => handleQuickTest(testIC)}
                          disabled={loading}
                          startIcon={<PlayArrowIcon />}
                        >
                          Test
                        </Button>
                      </Box>
                    ))}
                  </Stack>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 3, backgroundColor: '#f5f5f5' }}>
                  <Typography variant="h6" gutterBottom>
                    Manual Entry Guide
                  </Typography>
                  <Typography variant="body2" paragraph>
                    Enter the exact text marking visible on the IC chip. This can include:
                  </Typography>
                  <ul style={{ marginTop: 0, paddingLeft: '20px' }}>
                    <li><Typography variant="body2">Model number (e.g., ATmega328P)</Typography></li>
                    <li><Typography variant="body2">Manufacturer code (e.g., TI, STM)</Typography></li>
                    <li><Typography variant="body2">Additional markings on the chip surface</Typography></li>
                  </ul>
                  
                  <Typography variant="subtitle2" sx={{ mt: 3, mb: 1 }}>
                    Test Data Information:
                  </Typography>
                  <Typography variant="body2" paragraph>
                    • <strong>Green chips:</strong> Known authentic ICs in database
                  </Typography>
                  <Typography variant="body2" paragraph>
                    • <strong>Red chips:</strong> Test fake ICs (should be flagged)
                  </Typography>
                  <Typography variant="body2" paragraph>
                    • Click chip name to fill text field, or "Test" for instant verification
                  </Typography>
                  
                  <Alert severity="info" sx={{ mt: 2 }}>
                    <strong>Tip:</strong> The system performs fuzzy matching and handles case-insensitive text
                  </Alert>
                  
                  <Alert severity="warning" sx={{ mt: 1 }}>
                    Test data helps demonstrate system capabilities with known results
                  </Alert>
                </Paper>
              </Grid>
            </Grid>
          )}
        </Box>
      </Paper>

      {result && <VerificationResult result={result} />}
    </Container>
  );
};

export default ScannerPage;
