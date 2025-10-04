const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const axios = require('axios');
require('dotenv').config();

const Verification = require('./models/Verification');

const app = express();

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// MongoDB Connection
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/ic_verification';

mongoose.connect(MONGODB_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true
})
.then(() => console.log('✓ Connected to MongoDB'))
.catch(err => console.error('✗ MongoDB connection error:', err));

// ML Model API URL (Flask server)
const ML_API_URL = process.env.ML_API_URL || 'http://localhost:5000/api';

// ==================== Routes ====================

// Health check
app.get('/api/health', async (req, res) => {
  try {
    const mlHealth = await axios.get(`${ML_API_URL}/health`);
    res.json({
      status: 'ok',
      database: mongoose.connection.readyState === 1 ? 'connected' : 'disconnected',
      mlModel: mlHealth.data.model_loaded ? 'loaded' : 'not loaded'
    });
  } catch (error) {
    res.json({
      status: 'degraded',
      database: mongoose.connection.readyState === 1 ? 'connected' : 'disconnected',
      mlModel: 'unavailable',
      error: error.message
    });
  }
});

// Verify IC from text
app.post('/api/verify-text', async (req, res) => {
  try {
    const { marking_text } = req.body;

    if (!marking_text) {
      return res.status(400).json({ error: 'Marking text is required' });
    }

    // Call ML model API
    const mlResponse = await axios.post(`${ML_API_URL}/verify-text`, {
      marking_text
    });

    const result = mlResponse.data;

    // Save verification to database
    const verification = new Verification({
      scannedText: marking_text,
      status: result.status,
      confidence: result.confidence,
      isValid: result.is_valid,
      matchedIC: result.matched_ic ? {
        icModel: result.matched_ic.ic_model,
        oemName: result.matched_ic.oem_name,
        packageType: result.matched_ic.package_type,
        markingText: result.matched_ic.marking_text,
        datasheetUrl: result.matched_ic.datasheet_url,
        releaseDate: result.matched_ic.release_date
      } : null,
      possibleMatches: result.possible_matches || [],
      message: result.message,
      verificationType: 'text',
      userAgent: req.headers['user-agent'],
      ipAddress: req.ip
    });

    await verification.save();

    res.json({
      ...result,
      verificationId: verification._id
    });

  } catch (error) {
    console.error('Error in verify-text:', error);
    res.status(500).json({ 
      error: 'Verification failed',
      details: error.message 
    });
  }
});

// Verify IC from image
app.post('/api/verify-image', async (req, res) => {
  try {
    const { image_base64 } = req.body;

    if (!image_base64) {
      return res.status(400).json({ error: 'Image data is required' });
    }

    // Call ML model API
    const mlResponse = await axios.post(`${ML_API_URL}/verify-image`, {
      image_base64
    });

    const result = mlResponse.data;

    // Save verification to database
    const verification = new Verification({
      scannedText: result.scanned_text || '',
      extractedText: result.extracted_text || '',
      status: result.status,
      confidence: result.confidence,
      isValid: result.is_valid,
      matchedIC: result.matched_ic ? {
        icModel: result.matched_ic.ic_model,
        oemName: result.matched_ic.oem_name,
        packageType: result.matched_ic.package_type,
        markingText: result.matched_ic.marking_text,
        datasheetUrl: result.matched_ic.datasheet_url,
        releaseDate: result.matched_ic.release_date
      } : null,
      possibleMatches: result.possible_matches || [],
      message: result.message,
      verificationType: 'image',
      imageData: image_base64.substring(0, 100) + '...', // Store truncated version
      userAgent: req.headers['user-agent'],
      ipAddress: req.ip
    });

    await verification.save();

    res.json({
      ...result,
      verificationId: verification._id
    });

  } catch (error) {
    console.error('Error in verify-image:', error);
    res.status(500).json({ 
      error: 'Verification failed',
      details: error.message 
    });
  }
});

// Get verification history
app.get('/api/verifications', async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const skip = (page - 1) * limit;

    const verifications = await Verification.find()
      .sort({ createdAt: -1 })
      .skip(skip)
      .limit(limit)
      .select('-imageData'); // Exclude image data for performance

    const total = await Verification.countDocuments();

    res.json({
      verifications,
      pagination: {
        current_page: page,
        total_pages: Math.ceil(total / limit),
        total_count: total,
        per_page: limit
      }
    });
  } catch (error) {
    console.error('Error fetching verifications:', error);
    res.status(500).json({ error: 'Failed to fetch verifications' });
  }
});

// Get single verification by ID
app.get('/api/verifications/:id', async (req, res) => {
  try {
    const verification = await Verification.findById(req.params.id);
    
    if (!verification) {
      return res.status(404).json({ error: 'Verification not found' });
    }

    res.json(verification);
  } catch (error) {
    console.error('Error fetching verification:', error);
    res.status(500).json({ error: 'Failed to fetch verification' });
  }
});

// Get verification statistics
app.get('/api/stats', async (req, res) => {
  try {
    const totalVerifications = await Verification.countDocuments();
    const authenticCount = await Verification.countDocuments({ status: 'AUTHENTIC' });
    const fraudCount = await Verification.countDocuments({ status: 'FRAUD/UNKNOWN' });

    // Get recent verifications
    const recentVerifications = await Verification.find()
      .sort({ createdAt: -1 })
      .limit(10)
      .select('scannedText status confidence createdAt matchedIC.oemName matchedIC.icModel');

    // Get manufacturer distribution
    const manufacturerStats = await Verification.aggregate([
      { $match: { 'matchedIC.oemName': { $exists: true, $ne: null } } },
      { $group: { 
        _id: '$matchedIC.oemName', 
        count: { $sum: 1 } 
      }},
      { $sort: { count: -1 } },
      { $limit: 10 }
    ]);

    res.json({
      total_verifications: totalVerifications,
      authentic_count: authenticCount,
      fraud_count: fraudCount,
      success_rate: totalVerifications > 0 ? (authenticCount / totalVerifications * 100).toFixed(2) : 0,
      recent_verifications: recentVerifications,
      top_manufacturers: manufacturerStats
    });
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ error: 'Failed to fetch statistics' });
  }
});

// Get IC database from ML model
app.get('/api/ic-database', async (req, res) => {
  try {
    const response = await axios.get(`${ML_API_URL}/ic-database`);
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching IC database:', error);
    res.status(500).json({ error: 'Failed to fetch IC database' });
  }
});

// Get IC stats from ML model
app.get('/api/ic-stats', async (req, res) => {
  try {
    const response = await axios.get(`${ML_API_URL}/ic-stats`);
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching IC stats:', error);
    res.status(500).json({ error: 'Failed to fetch IC statistics' });
  }
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

// Error handler
app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({ 
    error: 'Internal server error',
    details: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log('='.repeat(60));
  console.log('IC Verification Backend Server');
  console.log('='.repeat(60));
  console.log(`✓ Server running on http://localhost:${PORT}`);
  console.log(`✓ ML API endpoint: ${ML_API_URL}`);
  console.log(`✓ MongoDB: ${MONGODB_URI}`);
  console.log('='.repeat(60));
  console.log('\nAvailable endpoints:');
  console.log('  GET  /api/health            - Health check');
  console.log('  POST /api/verify-text       - Verify IC from text');
  console.log('  POST /api/verify-image      - Verify IC from image');
  console.log('  GET  /api/verifications     - Get verification history');
  console.log('  GET  /api/verifications/:id - Get specific verification');
  console.log('  GET  /api/stats             - Get statistics');
  console.log('  GET  /api/ic-database       - Get IC database');
  console.log('  GET  /api/ic-stats          - Get IC statistics');
  console.log('='.repeat(60));
});

module.exports = app;
