import React, { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Typography,
  Alert
} from '@mui/material';
import CameraAltIcon from '@mui/icons-material/CameraAlt';
import CameraswitchIcon from '@mui/icons-material/Cameraswitch';

const WebcamScanner = ({ onCapture, loading }) => {
  const webcamRef = useRef(null);
  const [facingMode, setFacingMode] = useState('environment'); // 'user' or 'environment'
  const [error, setError] = useState(null);

  const videoConstraints = {
    width: 1280,
    height: 720,
    facingMode: facingMode
  };

  const capture = useCallback(() => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      if (imageSrc) {
        onCapture(imageSrc);
        setError(null);
      } else {
        setError('Failed to capture image');
      }
    }
  }, [webcamRef, onCapture]);

  const switchCamera = () => {
    setFacingMode(prev => prev === 'user' ? 'environment' : 'user');
  };

  const handleUserMediaError = (error) => {
    console.error('Webcam error:', error);
    setError('Failed to access camera. Please check permissions.');
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Camera Scanner
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ position: 'relative', borderRadius: 2, overflow: 'hidden' }}>
          <Webcam
            audio={false}
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            videoConstraints={videoConstraints}
            onUserMediaError={handleUserMediaError}
            style={{
              width: '100%',
              height: 'auto',
              maxHeight: '500px',
              display: 'block'
            }}
          />
          
          {loading && (
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 'rgba(0, 0, 0, 0.5)'
              }}
            >
              <CircularProgress />
            </Box>
          )}
        </Box>

        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
          <Button
            variant="contained"
            color="primary"
            fullWidth
            startIcon={<CameraAltIcon />}
            onClick={capture}
            disabled={loading}
          >
            Capture & Verify
          </Button>
          
          <Button
            variant="outlined"
            onClick={switchCamera}
            disabled={loading}
            startIcon={<CameraswitchIcon />}
          >
            Switch
          </Button>
        </Box>

        <Typography variant="caption" sx={{ display: 'block', mt: 2, textAlign: 'center', color: 'text.secondary' }}>
          Position the IC chip marking within the camera frame
        </Typography>
      </CardContent>
    </Card>
  );
};

export default WebcamScanner;
