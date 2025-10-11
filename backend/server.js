const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const axios = require('axios');
require('dotenv').config();

const Verification = require('./models/Verification');
const ICData = require('./models/ICData');
const IntegratedMLService = require('./services/ml_service');

const app = express();

// Initialize Integrated ML Service
const mlService = new IntegratedMLService();

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
    const systemStats = await mlService.getSystemStats();
    
    res.json({
      status: 'ok',
      database: mongoose.connection.readyState === 1 ? 'connected' : 'disconnected',
      mlModel: mlHealth.data.model_loaded ? 'loaded' : 'not loaded',
      integratedML: 'available',
      intelligentSearch: 'enabled',
      systemStats: systemStats
    });
  } catch (error) {
    res.json({
      status: 'degraded',
      database: mongoose.connection.readyState === 1 ? 'connected' : 'disconnected',
      mlModel: 'unavailable',
      integratedML: 'limited',
      error: error.message
    });
  }
});

// Comprehensive IC verification (new intelligent endpoint)
app.post('/api/comprehensive-verify', async (req, res) => {
  try {
    const { marking_text, image_base64 } = req.body;

    if (!marking_text && !image_base64) {
      return res.status(400).json({ error: 'Either marking text or image is required' });
    }

    console.log(`🚀 Comprehensive verification request for: ${marking_text}`);
    
    // Convert base64 to buffer if image provided
    let imageBuffer = null;
    if (image_base64) {
      const base64Data = image_base64.replace(/^data:image\/\w+;base64,/, '');
      imageBuffer = Buffer.from(base64Data, 'base64');
    }

    // Use the integrated ML service for comprehensive verification
    const result = await mlService.comprehensiveVerification(marking_text, imageBuffer);
    
    res.json({
      ...result.finalResult,
      comprehensive_results: {
        methods_used: Object.keys(result.methods),
        confidence_score: result.confidence,
        recommendations: result.recommendations,
        method_results: result.methods,
        processing_time: Date.now() - result.timestamp.getTime()
      },
      verificationId: result.verification?._id
    });

  } catch (error) {
    console.error('Error in comprehensive verification:', error);
    res.status(500).json({ 
      error: 'Comprehensive verification failed',
      details: error.message 
    });
  }
});

// Intelligent search endpoint
app.post('/api/intelligent-search', async (req, res) => {
  try {
    const { ic_part_number } = req.body;

    if (!ic_part_number) {
      return res.status(400).json({ error: 'IC part number is required' });
    }

    console.log(`🔍 Intelligent search request for: ${ic_part_number}`);
    
    const searchResult = await mlService.performIntelligentSearch(ic_part_number);
    
    // Update database with found information
    if (searchResult.status === 'success' && searchResult.processed_documents > 0) {
      await mlService.updateDatabaseFromSearch(ic_part_number, searchResult);
    }
    
    res.json({
      ...searchResult,
      database_updated: searchResult.status === 'success' && searchResult.processed_documents > 0
    });

  } catch (error) {
    console.error('Error in intelligent search:', error);
    res.status(500).json({ 
      error: 'Intelligent search failed',
      details: error.message 
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

// Get IC stats from ML model (enhanced)
app.get('/api/ic-stats', async (req, res) => {
  try {
    // Get stats from both ML model and database
    const [mlStats, dbStats] = await Promise.allSettled([
      axios.get(`${ML_API_URL}/ic-stats`),
      ICData.getStatistics()
    ]);
    
    const response = {
      traditional_ml: mlStats.status === 'fulfilled' ? mlStats.value.data : { error: 'unavailable' },
      database_stats: dbStats.status === 'fulfilled' ? dbStats.value[0] : { error: 'unavailable' },
      enhanced_features: {
        intelligent_search: 'enabled',
        internet_updates: 'active',
        comprehensive_verification: 'available'
      }
    };
    
    res.json(response);
  } catch (error) {
    console.error('Error fetching IC stats:', error);
    res.status(500).json({ error: 'Failed to fetch IC statistics' });
  }
});

// Get IC database (enhanced with intelligent search results)
app.get('/api/ic-database', async (req, res) => {
  try {
    const { search, limit = 50, category } = req.query;
    
    let query = { isActive: true };
    if (category) {
      query['specifications.category'] = category;
    }
    
    let icData;
    if (search) {
      icData = await ICData.searchByText(search, { limit: parseInt(limit) });
    } else {
      icData = await ICData.find(query)
        .limit(parseInt(limit))
        .sort({ popularity: -1, updatedAt: -1 });
    }
    
    const totalCount = await ICData.countDocuments(query);
    const categories = await ICData.distinct('specifications.category');
    const manufacturers = await ICData.distinct('manufacturer');
    
    res.json({
      ic_data: icData,
      total_count: totalCount,
      categories: categories,
      manufacturers: manufacturers,
      search_query: search,
      intelligent_search_enabled: true
    });
    
  } catch (error) {
    console.error('Error fetching IC database:', error);
    res.status(500).json({ error: 'Failed to fetch IC database' });
  }
});

// Get popular ICs
app.get('/api/popular-ics', async (req, res) => {
  try {
    const { limit = 10 } = req.query;
    const popularICs = await ICData.getPopularICs(parseInt(limit));
    
    res.json({
      popular_ics: popularICs,
      timestamp: new Date()
    });
  } catch (error) {
    console.error('Error fetching popular ICs:', error);
    res.status(500).json({ error: 'Failed to fetch popular ICs' });
  }
});

// Update IC data from internet (manual trigger)
app.post('/api/update-ic-data', async (req, res) => {
  try {
    const { ic_part_number } = req.body;
    
    if (!ic_part_number) {
      // Run background update for multiple ICs
      const updatePromise = mlService.updateICDataFromInternet();
      res.json({
        message: 'Background IC data update started',
        status: 'processing'
      });
      
      // Don't wait for completion
      return;
    }
    
    // Update specific IC
    const searchResult = await mlService.performIntelligentSearch(ic_part_number);
    
    if (searchResult.status === 'success') {
      await mlService.updateDatabaseFromSearch(ic_part_number, searchResult);
      
      res.json({
        message: `IC data updated for ${ic_part_number}`,
        status: 'success',
        documents_found: searchResult.found_documents || 0,
        documents_processed: searchResult.processed_documents || 0
      });
    } else {
      res.json({
        message: `No new data found for ${ic_part_number}`,
        status: 'no_data',
        search_result: searchResult
      });
    }
    
  } catch (error) {
    console.error('Error updating IC data:', error);
    res.status(500).json({ 
      error: 'Failed to update IC data',
      details: error.message 
    });
  }
});

// Get IC details with marking information
app.get('/api/ic-details/:partNumber', async (req, res) => {
  try {
    const { partNumber } = req.params;
    const icData = await ICData.findByPartNumber(partNumber);
    
    if (!icData) {
      return res.status(404).json({ 
        error: 'IC not found',
        suggestion: 'Try intelligent search to find and add this IC'
      });
    }
    
    res.json({
      ic_data: icData,
      marking_information: icData.markingInformation,
      document_sources: icData.documentSources,
      verification_history: icData.verificationHistory.slice(-10), // Last 10 verifications
      data_quality: icData.dataQuality
    });
    
  } catch (error) {
    console.error('Error fetching IC details:', error);
    res.status(500).json({ error: 'Failed to fetch IC details' });
  }
});

// Create or update IC data entry
app.post('/api/ic-data', async (req, res) => {
  try {
    const icData = req.body;
    
    // Check if IC already exists
    const existingIC = await ICData.findByPartNumber(icData.partNumber);
    
    let result;
    if (existingIC) {
      // Update existing IC
      result = await ICData.findByIdAndUpdate(
        existingIC._id,
        { 
          ...icData, 
          updatedAt: new Date(),
          'dataQuality.lastUpdated': new Date()
        },
        { new: true, runValidators: true }
      );
    } else {
      // Create new IC
      const newIC = new ICData({
        ...icData,
        createdAt: new Date(),
        updatedAt: new Date(),
        dataQuality: {
          completeness: calculateCompleteness(icData),
          verified: false,
          lastUpdated: new Date(),
          sources: icData.documentSources?.map(doc => doc.source) || []
        }
      });
      result = await newIC.save();
    }
    
    res.json({
      message: existingIC ? 'IC data updated successfully' : 'IC data created successfully',
      ic_data: result,
      operation: existingIC ? 'update' : 'create'
    });
    
  } catch (error) {
    console.error('Error creating/updating IC data:', error);
    res.status(500).json({ 
      error: 'Failed to create/update IC data',
      details: error.message 
    });
  }
});

// Delete IC data entry
app.delete('/api/ic-data/:partNumber', async (req, res) => {
  try {
    const { partNumber } = req.params;
    const { soft_delete = true } = req.query;
    
    let result;
    if (soft_delete === 'true') {
      // Soft delete - mark as inactive
      result = await ICData.findOneAndUpdate(
        { partNumber: partNumber },
        { 
          isActive: false,
          updatedAt: new Date(),
          deletedAt: new Date()
        },
        { new: true }
      );
    } else {
      // Hard delete
      result = await ICData.findOneAndDelete({ partNumber: partNumber });
    }
    
    if (!result) {
      return res.status(404).json({ error: 'IC not found' });
    }
    
    res.json({
      message: `IC data ${soft_delete === 'true' ? 'deactivated' : 'deleted'} successfully`,
      part_number: partNumber,
      operation: soft_delete === 'true' ? 'soft_delete' : 'hard_delete'
    });
    
  } catch (error) {
    console.error('Error deleting IC data:', error);
    res.status(500).json({ error: 'Failed to delete IC data' });
  }
});

// Batch operations for IC data
app.post('/api/ic-data/batch', async (req, res) => {
  try {
    const { operation, ic_data, part_numbers } = req.body;
    
    let results = [];
    
    switch (operation) {
      case 'create':
        if (!ic_data || !Array.isArray(ic_data)) {
          return res.status(400).json({ error: 'Invalid IC data array provided' });
        }
        
        for (const icItem of ic_data) {
          try {
            const newIC = new ICData({
              ...icItem,
              createdAt: new Date(),
              updatedAt: new Date(),
              dataQuality: {
                completeness: calculateCompleteness(icItem),
                verified: false,
                lastUpdated: new Date(),
                sources: icItem.documentSources?.map(doc => doc.source) || []
              }
            });
            const result = await newIC.save();
            results.push({ status: 'success', part_number: icItem.partNumber, data: result });
          } catch (error) {
            results.push({ status: 'error', part_number: icItem.partNumber, error: error.message });
          }
        }
        break;
        
      case 'delete':
        if (!part_numbers || !Array.isArray(part_numbers)) {
          return res.status(400).json({ error: 'Invalid part numbers array provided' });
        }
        
        for (const partNumber of part_numbers) {
          try {
            const result = await ICData.findOneAndUpdate(
              { partNumber: partNumber },
              { 
                isActive: false,
                updatedAt: new Date(),
                deletedAt: new Date()
              }
            );
            
            if (result) {
              results.push({ status: 'success', part_number: partNumber });
            } else {
              results.push({ status: 'not_found', part_number: partNumber });
            }
          } catch (error) {
            results.push({ status: 'error', part_number: partNumber, error: error.message });
          }
        }
        break;
        
      case 'update_quality':
        if (!part_numbers || !Array.isArray(part_numbers)) {
          return res.status(400).json({ error: 'Invalid part numbers array provided' });
        }
        
        for (const partNumber of part_numbers) {
          try {
            const icData = await ICData.findOne({ partNumber });
            if (icData) {
              icData.dataQuality.completeness = calculateCompleteness(icData.toObject());
              icData.dataQuality.lastUpdated = new Date();
              await icData.save();
              results.push({ status: 'success', part_number: partNumber, quality: icData.dataQuality });
            } else {
              results.push({ status: 'not_found', part_number: partNumber });
            }
          } catch (error) {
            results.push({ status: 'error', part_number: partNumber, error: error.message });
          }
        }
        break;
        
      default:
        return res.status(400).json({ error: 'Invalid batch operation' });
    }
    
    res.json({
      message: `Batch ${operation} operation completed`,
      results: results,
      total_processed: results.length,
      successful: results.filter(r => r.status === 'success').length,
      failed: results.filter(r => r.status === 'error').length
    });
    
  } catch (error) {
    console.error('Error in batch operation:', error);
    res.status(500).json({ error: 'Failed to execute batch operation' });
  }
});

// Data quality assessment endpoint
app.get('/api/data-quality', async (req, res) => {
  try {
    const qualityStats = await ICData.aggregate([
      { $match: { isActive: true } },
      {
        $group: {
          _id: null,
          totalRecords: { $sum: 1 },
          averageCompleteness: { $avg: '$dataQuality.completeness' },
          verifiedRecords: { 
            $sum: { $cond: ['$dataQuality.verified', 1, 0] } 
          },
          recordsWithSources: {
            $sum: { $cond: [{ $gt: [{ $size: '$documentSources' }, 0] }, 1, 0] }
          },
          recordsByCategory: {
            $push: '$specifications.category'
          }
        }
      }
    ]);
    
    const categoryDistribution = await ICData.aggregate([
      { $match: { isActive: true } },
      { $group: { _id: '$specifications.category', count: { $sum: 1 } } },
      { $sort: { count: -1 } }
    ]);
    
    const manufacturerDistribution = await ICData.aggregate([
      { $match: { isActive: true } },
      { $group: { _id: '$manufacturer', count: { $sum: 1 } } },
      { $sort: { count: -1 } },
      { $limit: 10 }
    ]);
    
    const lowQualityRecords = await ICData.find({
      isActive: true,
      'dataQuality.completeness': { $lt: 0.7 }
    }).limit(20).select('partNumber dataQuality.completeness manufacturer');
    
    res.json({
      overall_quality: qualityStats[0] || {},
      category_distribution: categoryDistribution,
      manufacturer_distribution: manufacturerDistribution,
      low_quality_records: lowQualityRecords,
      recommendations: {
        improve_completeness: lowQualityRecords.length,
        verify_records: (qualityStats[0]?.totalRecords || 0) - (qualityStats[0]?.verifiedRecords || 0),
        add_sources: (qualityStats[0]?.totalRecords || 0) - (qualityStats[0]?.recordsWithSources || 0)
      }
    });
    
  } catch (error) {
    console.error('Error fetching data quality stats:', error);
    res.status(500).json({ error: 'Failed to fetch data quality statistics' });
  }
});

// Helper function to calculate data completeness
function calculateCompleteness(icData) {
  const requiredFields = [
    'partNumber', 'manufacturer', 'specifications.category',
    'specifications.description', 'markingInformation.standardMarkings'
  ];
  
  const optionalFields = [
    'specifications.package', 'specifications.pinCount',
    'specifications.operatingVoltage', 'specifications.operatingTemperature',
    'markingInformation.lotCodes', 'markingInformation.dateCodes',
    'documentSources'
  ];
  
  let score = 0;
  const totalFields = requiredFields.length + optionalFields.length;
  
  // Required fields (higher weight)
  for (const field of requiredFields) {
    if (getNestedValue(icData, field)) {
      score += 2; // Required fields count double
    }
  }
  
  // Optional fields
  for (const field of optionalFields) {
    if (getNestedValue(icData, field)) {
      score += 1;
    }
  }
  
  // Maximum possible score: (required * 2) + optional
  const maxScore = (requiredFields.length * 2) + optionalFields.length;
  return Math.min(score / maxScore, 1.0);
}

// Helper function to get nested object values
function getNestedValue(obj, path) {
  return path.split('.').reduce((current, key) => {
    return current && current[key] !== undefined && current[key] !== null && current[key] !== '' 
      ? current[key] 
      : null;
  }, obj);
}

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
