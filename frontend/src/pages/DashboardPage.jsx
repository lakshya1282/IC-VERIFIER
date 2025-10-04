import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CircularProgress
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import MemoryIcon from '@mui/icons-material/Memory';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { getStats, getICStats } from '../services/api';

const StatCard = ({ title, value, icon, color }) => (
  <Card>
    <CardContent>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography color="text.secondary" variant="subtitle2">
            {title}
          </Typography>
          <Typography variant="h4" sx={{ mt: 1 }}>
            {value}
          </Typography>
        </Box>
        <Box
          sx={{
            backgroundColor: color,
            borderRadius: 2,
            p: 1.5,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const DashboardPage = () => {
  const [stats, setStats] = useState(null);
  const [icStats, setICStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsData, icStatsData] = await Promise.all([
        getStats(),
        getICStats()
      ]);
      setStats(statsData);
      setICStats(icStatsData);
      setError(null);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Typography color="error">{error}</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Overview of IC verification system performance
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Verifications"
            value={stats?.total_verifications || 0}
            icon={<MemoryIcon sx={{ color: 'white', fontSize: 32 }} />}
            color="#2196f3"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Authentic"
            value={stats?.authentic_count || 0}
            icon={<CheckCircleIcon sx={{ color: 'white', fontSize: 32 }} />}
            color="#4caf50"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Fraud/Unknown"
            value={stats?.fraud_count || 0}
            icon={<CancelIcon sx={{ color: 'white', fontSize: 32 }} />}
            color="#f44336"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Success Rate"
            value={`${stats?.success_rate || 0}%`}
            icon={<TrendingUpIcon sx={{ color: 'white', fontSize: 32 }} />}
            color="#ff9800"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              IC Database Statistics
            </Typography>
            {icStats && (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography>Total IC Models:</Typography>
                  <Typography fontWeight="bold">{icStats.total_ic_models}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography>Manufacturers:</Typography>
                  <Typography fontWeight="bold">{icStats.total_manufacturers}</Typography>
                </Box>
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Registered Manufacturers:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                    {icStats.manufacturers?.map((mfr, idx) => (
                      <Box
                        key={idx}
                        sx={{
                          px: 1.5,
                          py: 0.5,
                          backgroundColor: '#e3f2fd',
                          borderRadius: 1,
                          fontSize: '0.875rem'
                        }}
                      >
                        {mfr}
                      </Box>
                    ))}
                  </Box>
                </Box>
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Top Manufacturers Verified
            </Typography>
            {stats?.top_manufacturers && stats.top_manufacturers.length > 0 ? (
              <Box>
                {stats.top_manufacturers.map((item, idx) => (
                  <Box
                    key={idx}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      mb: 1.5,
                      pb: 1,
                      borderBottom: idx < stats.top_manufacturers.length - 1 ? '1px solid #e0e0e0' : 'none'
                    }}
                  >
                    <Typography>{item._id}</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box
                        sx={{
                          width: 100,
                          height: 8,
                          backgroundColor: '#e0e0e0',
                          borderRadius: 4,
                          overflow: 'hidden'
                        }}
                      >
                        <Box
                          sx={{
                            width: `${(item.count / stats.authentic_count) * 100}%`,
                            height: '100%',
                            backgroundColor: '#2196f3'
                          }}
                        />
                      </Box>
                      <Typography fontWeight="bold">{item.count}</Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography color="text.secondary">No verification data available yet</Typography>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Verifications
            </Typography>
            {stats?.recent_verifications && stats.recent_verifications.length > 0 ? (
              <Box>
                {stats.recent_verifications.map((verification, idx) => (
                  <Box
                    key={idx}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      p: 2,
                      mb: 1,
                      backgroundColor: verification.status === 'AUTHENTIC' ? '#e8f5e9' : '#fff3e0',
                      borderRadius: 1
                    }}
                  >
                    <Box>
                      <Typography variant="body2" fontFamily="monospace">
                        {verification.scannedText}
                      </Typography>
                      {verification.matchedIC?.oemName && (
                        <Typography variant="caption" color="text.secondary">
                          {verification.matchedIC.oemName} - {verification.matchedIC.icModel}
                        </Typography>
                      )}
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Typography variant="caption">
                        {(verification.confidence * 100).toFixed(1)}%
                      </Typography>
                      <Box
                        sx={{
                          px: 1.5,
                          py: 0.5,
                          backgroundColor: verification.status === 'AUTHENTIC' ? '#4caf50' : '#ff9800',
                          color: 'white',
                          borderRadius: 1,
                          fontSize: '0.75rem',
                          fontWeight: 'bold'
                        }}
                      >
                        {verification.status}
                      </Box>
                    </Box>
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography color="text.secondary">No verifications performed yet</Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default DashboardPage;
