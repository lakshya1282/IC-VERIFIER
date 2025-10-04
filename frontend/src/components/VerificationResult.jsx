import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Alert,
  Table,
  TableBody,
  TableRow,
  TableCell,
  Link,
  Divider
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';

const VerificationResult = ({ result }) => {
  if (!result) return null;

  const isAuthentic = result.status === 'AUTHENTIC';

  return (
    <Card sx={{ mt: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">
            Verification Result
          </Typography>
          <Chip
            icon={isAuthentic ? <CheckCircleIcon /> : <CancelIcon />}
            label={result.status}
            color={isAuthentic ? 'success' : 'error'}
            size="medium"
          />
        </Box>

        <Alert severity={isAuthentic ? 'success' : 'warning'} sx={{ mb: 2 }}>
          {result.message}
        </Alert>

        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Scanned Text:
          </Typography>
          <Typography variant="body1" sx={{ fontFamily: 'monospace', mb: 1 }}>
            {result.scanned_text || result.extractedText || 'N/A'}
          </Typography>

          {result.extracted_text && (
            <>
              <Typography variant="body2" color="text.secondary">
                Extracted Text (OCR):
              </Typography>
              <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                {result.extracted_text}
              </Typography>
            </>
          )}
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Confidence Score:
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Box
              sx={{
                flex: 1,
                height: 8,
                backgroundColor: '#e0e0e0',
                borderRadius: 4,
                overflow: 'hidden',
                mr: 2
              }}
            >
              <Box
                sx={{
                  height: '100%',
                  width: `${result.confidence * 100}%`,
                  backgroundColor: isAuthentic ? '#4caf50' : '#ff9800',
                  transition: 'width 0.3s ease'
                }}
              />
            </Box>
            <Typography variant="body1" fontWeight="bold">
              {(result.confidence * 100).toFixed(1)}%
            </Typography>
          </Box>
        </Box>

        {result.matched_ic && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="h6" gutterBottom>
              IC Details
            </Typography>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell><strong>Model Number:</strong></TableCell>
                  <TableCell>{result.matched_ic.ic_model}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Manufacturer:</strong></TableCell>
                  <TableCell>{result.matched_ic.oem_name}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Package Type:</strong></TableCell>
                  <TableCell>{result.matched_ic.package_type}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Marking Text:</strong></TableCell>
                  <TableCell sx={{ fontFamily: 'monospace' }}>
                    {result.matched_ic.marking_text}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Release Date:</strong></TableCell>
                  <TableCell>{result.matched_ic.release_date}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Datasheet:</strong></TableCell>
                  <TableCell>
                    <Link
                      href={result.matched_ic.datasheet_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View Datasheet
                    </Link>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </>
        )}

        {result.possible_matches && result.possible_matches.length > 0 && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="h6" gutterBottom>
              Possible Matches
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              These ICs have similar markings:
            </Typography>
            {result.possible_matches.map((match, index) => (
              <Box key={index} sx={{ mb: 1, p: 1, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
                <Typography variant="body2">
                  <strong>{match.oem_name}</strong> - {match.ic_model}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Marking: {match.marking_text} | Similarity: {(match.similarity * 100).toFixed(1)}%
                </Typography>
              </Box>
            ))}
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default VerificationResult;
