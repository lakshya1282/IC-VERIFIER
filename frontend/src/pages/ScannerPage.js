import React, { useState, useRef, useCallback } from 'react';
import {
  Box,
  Paper,
  Tabs,
  Tab,
  Typography,
  Button,
  TextField,
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  IconButton
} from '@mui/material';
import {
  CameraAlt,
  PhotoCamera,
  Upload,
  TextFields,
  Memory,
  CheckCircle,
  Error,
  Warning,
  ContentCopy,
  PlayArrow
} from '@mui/icons-material';
import { verifyICText, verifyICImage, comprehensiveVerification } from '../services/api';

// Test IC data for quick testing
const TEST_IC_DATA = [
  'STM32F103C8T6',
  'ATmega328P',
  'ESP32-WROOM-32',
  'LM555CN',
  'TL071CN',
  'NE555P',
  'ATtiny85',
  'PIC16F877A',
  'LM358N',
  'CD4017BE',
  'SN74LS00N',
  'LM7805',
  'DS18B20',
  'HC-SR04',
  'ESP8266',
  'Arduino Nano',
  'ATMEGA2560',
  'STM32F407VGT6',
  'TMS320F28335',
  'XC7A35T'
];

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`scanner-tabpanel-${index}`}
      aria-labelledby={`scanner-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export default function ScannerPage() {
  const [tabValue, setTabValue] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  
  // Camera scan states
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  
  // Upload image states
  const [selectedFile, setSelectedFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  
  // Manual text entry states
  const [manualText, setManualText] = useState('');

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setResult(null);
    setError(null);
  };

  // Camera functions
  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } 
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsCameraActive(true);
        setError(null);
      }
    } catch (err) {
      setError('Camera access denied. Please allow camera access and try again.');
      console.error('Camera error:', err);
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
      setIsCameraActive(false);
    }
  }, []);

  const captureImage = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const video = videoRef.current;
    const context = canvas.getContext('2d');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);
    
    // Convert to blob and verify
    canvas.toBlob(async (blob) => {
      await handleImageVerification(blob);
    }, 'image/jpeg', 0.8);
  }, []);

  // File upload functions
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff'];
      if (!validTypes.includes(file.type)) {
        setError('Please select a valid image file (JPEG, PNG, BMP, or TIFF)');
        return;
      }
      
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB');
        return;
      }
      
      setSelectedFile(file);
      setError(null);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUploadVerification = async () => {
    if (!selectedFile) {
      setError('Please select an image file first');
      return;
    }
    
    await handleImageVerification(selectedFile);
  };

  // Verification functions
  const handleImageVerification = async (imageData) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    
    try {
      // Try comprehensive verification first if available
      let response;
      try {
        response = await comprehensiveVerification(imageData);
      } catch (err) {
        // Fallback to regular image verification
        response = await verifyICImage(imageData);
      }
      
      setResult(response);
    } catch (err) {
      setError(`Verification failed: ${err.message || 'Unknown error'}`);
      console.error('Image verification error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTextVerification = async (text = manualText) => {
    if (!text.trim()) {
      setError('Please enter IC marking text');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const response = await verifyICText(text.trim());
      setResult(response);
    } catch (err) {
      setError(`Verification failed: ${err.message || 'Unknown error'}`);
      console.error('Text verification error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      // Could add a toast notification here
    });
  };

  const fillManualText = (text) => {
    setManualText(text);
  };

  const quickTestIC = async (text) => {
    setManualText(text);
    await handleTextVerification(text);
  };

  // Result display component
  const ResultDisplay = ({ result }) => {
    if (!result) return null;

    const isAuthentic = result.status === 'AUTHENTIC' || result.status === 'authentic';
    const statusColor = isAuthentic ? 'success' : 'error';
    const StatusIcon = isAuthentic ? CheckCircle : Error;
    
    return (
      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Box display="flex" alignItems="center" gap={1}>
                <StatusIcon color={statusColor} />
                <Typography variant="h6">
                  Verification Result
                </Typography>
                <Chip 
                  label={result.status} 
                  color={statusColor}
                  variant="outlined"
                />
              </Box>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="textSecondary">
                Scanned Text
              </Typography>
              <Typography variant="body1">
                {result.scannedText || result.extracted_text || 'N/A'}
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="textSecondary">
                Confidence
              </Typography>
              <Typography variant="body1">
                {((result.confidence || 0) * 100).toFixed(1)}%
              </Typography>
            </Grid>
            
            {result.matchedIC && (
              <>
                <Grid item xs={12}>
                  <Divider />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="textSecondary">
                    Manufacturer
                  </Typography>
                  <Typography variant="body1">
                    {result.matchedIC.oemName || result.matchedIC.manufacturer || 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="textSecondary">
                    IC Model
                  </Typography>
                  <Typography variant="body1">
                    {result.matchedIC.icModel || result.matchedIC.model || 'N/A'}
                  </Typography>
                </Grid>
                {result.matchedIC.description && (
                  <Grid item xs={12}>
                    <Typography variant="body2" color="textSecondary">
                      Description
                    </Typography>
                    <Typography variant="body1">
                      {result.matchedIC.description}
                    </Typography>
                  </Grid>
                )}
              </>
            )}
            
            {result.analysis && (
              <>
                <Grid item xs={12}>
                  <Divider />
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">
                    Analysis
                  </Typography>
                  <Typography variant="body1">
                    {result.analysis}
                  </Typography>
                </Grid>
              </>
            )}
            
            <Grid item xs={12}>
              <Typography variant="caption" color="textSecondary">
                Verified at: {new Date().toLocaleString()}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        IC Scanner & Verification
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Scan, upload, or manually enter IC markings to verify authenticity
      </Typography>

      <Paper sx={{ mt: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="scanner tabs">
          <Tab 
            label="Camera Scan" 
            icon={<CameraAlt />} 
            iconPosition="start"
          />
          <Tab 
            label="Upload Image" 
            icon={<Upload />} 
            iconPosition="start"
          />
          <Tab 
            label="Manual Entry" 
            icon={<TextFields />} 
            iconPosition="start"
          />
        </Tabs>

        {/* Camera Scan Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Box 
                sx={{ 
                  position: 'relative',
                  bgcolor: 'grey.100',
                  borderRadius: 1,
                  minHeight: 300,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                {isCameraActive ? (
                  <>
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      style={{
                        width: '100%',
                        height: 'auto',
                        maxHeight: 400,
                        borderRadius: 4
                      }}
                    />
                    <canvas ref={canvasRef} style={{ display: 'none' }} />
                  </>
                ) : (
                  <Box textAlign="center">
                    <PhotoCamera sx={{ fontSize: 60, color: 'grey.400', mb: 2 }} />
                    <Typography variant="h6" color="textSecondary">
                      Camera Preview
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Start camera to begin scanning
                    </Typography>
                  </Box>
                )}
              </Box>
              
              <Box sx={{ mt: 2, display: 'flex', gap: 2, justifyContent: 'center' }}>
                {!isCameraActive ? (
                  <Button
                    variant="contained"
                    startIcon={<CameraAlt />}
                    onClick={startCamera}
                  >
                    Start Camera
                  </Button>
                ) : (
                  <>
                    <Button
                      variant="contained"
                      color="success"
                      startIcon={<PhotoCamera />}
                      onClick={captureImage}
                      disabled={isLoading}
                    >
                      {isLoading ? 'Processing...' : 'Capture & Verify'}
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={stopCamera}
                      disabled={isLoading}
                    >
                      Stop Camera
                    </Button>
                  </>
                )}
              </Box>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom>
                Instructions
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="1. Start Camera" 
                    secondary="Allow camera access in your browser"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="2. Position IC" 
                    secondary="Center the IC marking in the camera view"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="3. Capture Image" 
                    secondary="Click capture when marking is clear"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="4. Verify Results" 
                    secondary="Review authenticity and details"
                  />
                </ListItem>
              </List>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Upload Image Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Box textAlign="center">
                <input
                  accept="image/*"
                  id="image-upload"
                  type="file"
                  style={{ display: 'none' }}
                  onChange={handleFileChange}
                />
                <label htmlFor="image-upload">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<Upload />}
                    sx={{ mb: 2 }}
                  >
                    Select Image File
                  </Button>
                </label>
                
                {imagePreview && (
                  <Box sx={{ mt: 2, mb: 2 }}>
                    <img
                      src={imagePreview}
                      alt="Preview"
                      style={{
                        maxWidth: '100%',
                        maxHeight: 300,
                        borderRadius: 4,
                        border: '1px solid #ddd'
                      }}
                    />
                  </Box>
                )}
                
                {selectedFile && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="textSecondary">
                      Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                    </Typography>
                  </Box>
                )}
                
                <Button
                  variant="contained"
                  startIcon={<Memory />}
                  onClick={handleUploadVerification}
                  disabled={!selectedFile || isLoading}
                  sx={{ mt: 1 }}
                >
                  {isLoading ? <CircularProgress size={20} /> : 'Verify IC'}
                </Button>
              </Box>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom>
                Image Guidelines
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="Supported Formats" 
                    secondary="JPEG, PNG, BMP, TIFF"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="File Size" 
                    secondary="Maximum 10MB per image"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Image Quality" 
                    secondary="Clear, well-lit, focused markings"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Resolution" 
                    secondary="Higher resolution for better OCR"
                  />
                </ListItem>
              </List>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Manual Entry Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="IC Marking Text"
                placeholder="Enter IC part number or marking (e.g., STM32F103C8T6)"
                value={manualText}
                onChange={(e) => setManualText(e.target.value)}
                multiline
                rows={3}
                sx={{ mb: 2 }}
              />
              
              <Box display="flex" gap={2} flexWrap="wrap" mb={2}>
                <Button
                  variant="contained"
                  startIcon={<Memory />}
                  onClick={() => handleTextVerification()}
                  disabled={!manualText.trim() || isLoading}
                >
                  {isLoading ? <CircularProgress size={20} /> : 'Verify IC'}
                </Button>
                
                <Button
                  variant="outlined"
                  onClick={() => setManualText('')}
                  disabled={isLoading}
                >
                  Clear
                </Button>
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="h6" gutterBottom>
                Quick Test ICs
              </Typography>
              <Typography variant="body2" color="textSecondary" paragraph>
                Click to fill or test common IC markings
              </Typography>
              
              <Box display="flex" flexWrap="wrap" gap={1}>
                {TEST_IC_DATA.map((ic, index) => (
                  <Box key={index} display="flex" alignItems="center">
                    <Chip
                      label={ic}
                      variant="outlined"
                      clickable
                      onClick={() => fillManualText(ic)}
                      sx={{ mr: 1 }}
                    />
                    <IconButton
                      size="small"
                      onClick={() => quickTestIC(ic)}
                      title={`Quick test ${ic}`}
                      disabled={isLoading}
                    >
                      <PlayArrow fontSize="small" />
                    </IconButton>
                  </Box>
                ))}
              </Box>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom>
                Tips for Manual Entry
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="Exact Matching" 
                    secondary="Enter the complete part number as printed"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Case Sensitive" 
                    secondary="Maintain original capitalization"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Remove Spaces" 
                    secondary="Most IC markings don't have spaces"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Test Data" 
                    secondary="Use the chips below for quick testing"
                  />
                </ListItem>
              </List>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading Display */}
      {isLoading && (
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2 }}>
          <CircularProgress size={20} />
          <Typography>Verifying IC...</Typography>
        </Box>
      )}

      {/* Result Display */}
      <ResultDisplay result={result} />
    </Box>
  );
}