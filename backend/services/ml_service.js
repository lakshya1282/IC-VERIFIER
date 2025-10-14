/**
 * Integrated ML Service for IC Verification
 * Combines traditional ML model, deep learning API, and intelligent internet search
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs').promises;
const axios = require('axios');
const ICData = require('../models/ICData');
const Verification = require('../models/Verification');

class IntegratedMLService {
  constructor() {
    this.deepLearningApiUrl = process.env.DEEP_LEARNING_API_URL || 'http://localhost:5000';
    this.mlModelPath = path.join(__dirname, '../../ml-model');
    this.intelligentSearchPath = path.join(__dirname, 'intelligent_search.py');
    
    // Initialize components
    this.initializeService();
  }

  async initializeService() {
    console.log('🤖 Initializing Integrated ML Service...');
    
    try {
      // Check if traditional ML model exists
      await this.checkTraditionalModel();
      
      // Check deep learning API connectivity
      await this.checkDeepLearningAPI();
      
      // Initialize intelligent search system
      await this.initializeIntelligentSearch();
      
      console.log('✅ Integrated ML Service initialized successfully!');
    } catch (error) {
      console.error('❌ Error initializing ML Service:', error.message);
    }
  }

  async checkTraditionalModel() {
    const modelPath = path.join(this.mlModelPath, 'ic_model.pkl');
    
    try {
      await fs.access(modelPath);
      console.log('✅ Traditional ML model found');
    } catch (error) {
      console.log('⚠️ Traditional ML model not found, training...');
      await this.trainTraditionalModel();
    }
  }

  async trainTraditionalModel() {
    return new Promise((resolve, reject) => {
      console.log('🏋️ Training traditional ML model...');
      
      const pythonProcess = spawn('python', ['train_model.py'], {
        cwd: this.mlModelPath,
        stdio: 'pipe'
      });

      let output = '';
      let errorOutput = '';

      pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
        console.log(`Training: ${data.toString().trim()}`);
      });

      pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
        console.error(`Training Error: ${data.toString().trim()}`);
      });

      pythonProcess.on('close', (code) => {
        if (code === 0) {
          console.log('✅ Traditional ML model trained successfully');
          resolve(output);
        } else {
          console.error('❌ Failed to train traditional ML model');
          reject(new Error(`Training failed with code ${code}: ${errorOutput}`));
        }
      });
    });
  }

  async checkDeepLearningAPI() {
    try {
      const response = await axios.get(`${this.deepLearningApiUrl}/health`, { timeout: 5000 });
      if (response.data.status === 'healthy') {
        console.log('✅ Deep Learning API is healthy');
        return true;
      }
    } catch (error) {
      console.log('⚠️ Deep Learning API not available:', error.message);
      return false;
    }
  }

  async initializeIntelligentSearch() {
    try {
      // Check if Python dependencies are available
      const testProcess = spawn('python', ['-c', 'import requests, BeautifulSoup4, PyPDF2'], {
        stdio: 'pipe'
      });

      return new Promise((resolve) => {
        testProcess.on('close', (code) => {
          if (code === 0) {
            console.log('✅ Intelligent search dependencies available');
            resolve(true);
          } else {
            console.log('⚠️ Some intelligent search dependencies missing');
            resolve(false);
          }
        });
      });
    } catch (error) {
      console.log('⚠️ Intelligent search initialization failed:', error.message);
      return false;
    }
  }

  /**
   * Comprehensive IC Verification using all available methods
   */
  async comprehensiveVerification(icText, imageData = null) {
    console.log(`🔍 Starting comprehensive verification for: ${icText}`);
    
    const results = {
      icText: icText,
      timestamp: new Date(),
      methods: {},
      finalResult: null,
      confidence: 0,
      recommendations: []
    };

    try {
      // Step 1: Try Deep Learning API first (highest accuracy)
      try {
        const dlResult = await this.verifyWithDeepLearning(icText, imageData);
        results.methods.deepLearning = dlResult;
        
        if (dlResult.status === 'AUTHENTIC' && dlResult.confidence > 0.8) {
          results.finalResult = dlResult;
          results.confidence = dlResult.confidence;
          results.recommendations.push('High confidence verification from deep learning model');
        }
      } catch (error) {
        console.log('⚠️ Deep learning verification failed:', error.message);
        results.methods.deepLearning = { error: error.message };
      }

      // Step 2: Traditional ML Model verification
      try {
        const mlResult = await this.verifyWithTraditionalML(icText);
        results.methods.traditionalML = mlResult;
        
        if (!results.finalResult && mlResult.status === 'AUTHENTIC') {
          results.finalResult = mlResult;
          results.confidence = mlResult.confidence;
          results.recommendations.push('Verification from traditional ML model');
        }
      } catch (error) {
        console.log('⚠️ Traditional ML verification failed:', error.message);
        results.methods.traditionalML = { error: error.message };
      }

      // Step 3: Database lookup
      try {
        const dbResult = await this.verifyFromDatabase(icText);
        results.methods.database = dbResult;
        
        if (!results.finalResult && dbResult.found) {
          results.finalResult = {
            status: 'AUTHENTIC',
            confidence: 0.9,
            matched_ic: dbResult.icData,
            message: 'Found in local database'
          };
          results.confidence = 0.9;
          results.recommendations.push('Found in verified local database');
        }
      } catch (error) {
        console.log('⚠️ Database verification failed:', error.message);
        results.methods.database = { error: error.message };
      }

      // Step 4: Web Scraping (manufacturer websites)
      if (!results.finalResult || results.confidence < 0.7) {
        try {
          console.log('🕷️ Performing web scraping search...');
          const scrapingResult = await this.performWebScraping(icText);
          results.methods.webScraping = scrapingResult;
          
          if (scrapingResult.status === 'success' && scrapingResult.results.length > 0) {
            // Update database with scraped information
            await this.updateDatabaseFromScraping(icText, scrapingResult);
            
            results.finalResult = {
              status: 'AUTHENTIC',
              confidence: 0.8,
              source: 'manufacturer_website',
              matched_ic: scrapingResult.results[0],
              message: 'Found via manufacturer website scraping'
            };
            results.confidence = 0.8;
            results.recommendations.push('Verified via manufacturer website data');
          }
        } catch (error) {
          console.log('⚠️ Web scraping failed:', error.message);
          results.methods.webScraping = { error: error.message };
        }
      }

      // Step 5: Intelligent Internet Search (fallback)
      if (!results.finalResult || results.confidence < 0.7) {
        try {
          console.log('🌐 Performing intelligent internet search...');
          const searchResult = await this.performIntelligentSearch(icText);
          results.methods.internetSearch = searchResult;
          
          if (searchResult.status === 'success' && searchResult.processed_documents > 0) {
            // Update database with new information
            await this.updateDatabaseFromSearch(icText, searchResult);
            
            results.finalResult = {
              status: 'AUTHENTIC',
              confidence: 0.8,
              message: 'Verified through internet documentation',
              sources: searchResult.documents?.length || 0
            };
            results.confidence = 0.8;
            results.recommendations.push(`Found ${searchResult.processed_documents} relevant documents online`);
          }
        } catch (error) {
          console.log('⚠️ Internet search failed:', error.message);
          results.methods.internetSearch = { error: error.message };
        }
      }

      // Step 5: Determine final result
      if (!results.finalResult) {
        results.finalResult = {
          status: 'UNKNOWN',
          confidence: 0.1,
          message: 'IC not found in any verification method'
        };
        results.recommendations.push('Consider manual verification or contact manufacturer');
      }

      // Step 6: Save verification record
      await this.saveVerificationRecord(results);

      console.log(`✅ Comprehensive verification completed: ${results.finalResult.status}`);
      return results;

    } catch (error) {
      console.error('❌ Comprehensive verification failed:', error);
      throw error;
    }
  }

  async verifyWithDeepLearning(icText, imageData = null) {
    const endpoint = imageData ? '/verify' : '/verify';
    
    try {
      let requestData;
      let headers = {};

      if (imageData) {
        // Create FormData for image
        const FormData = require('form-data');
        const formData = new FormData();
        formData.append('image', imageData, 'ic_image.jpg');
        requestData = formData;
        headers = formData.getHeaders();
      } else {
        // Text verification
        const FormData = require('form-data');
        const formData = new FormData();
        formData.append('text', icText);
        requestData = formData;
        headers = formData.getHeaders();
      }

      const response = await axios.post(`${this.deepLearningApiUrl}${endpoint}`, requestData, {
        headers: headers,
        timeout: 30000
      });

      return response.data;
    } catch (error) {
      console.error('Deep learning API error:', error.message);
      throw error;
    }
  }

  async verifyWithTraditionalML(icText) {
    return new Promise((resolve, reject) => {
      const pythonScript = `
import sys
import os
sys.path.append('${this.mlModelPath}')

try:
    from train_model import ICVerificationModel
    model = ICVerificationModel.load_model('${path.join(this.mlModelPath, 'ic_model.pkl')}')
    result = model.verify_ic('${icText}')
    print('ML_RESULT:' + str(result).replace("'", '"'))
except Exception as e:
    print('ML_ERROR:' + str(e))
`;

      const pythonProcess = spawn('python', ['-c', pythonScript], {
        stdio: 'pipe'
      });

      let output = '';
      let errorOutput = '';

      pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });

      pythonProcess.on('close', (code) => {
        try {
          const lines = output.trim().split('\n');
          const resultLine = lines.find(line => line.startsWith('ML_RESULT:'));
          
          if (resultLine) {
            const resultStr = resultLine.replace('ML_RESULT:', '');
            // Simple parsing since Python dict format might not be valid JSON
            const result = eval('(' + resultStr + ')'); // Note: eval is not recommended for production
            resolve(result);
          } else {
            const errorLine = lines.find(line => line.startsWith('ML_ERROR:'));
            const errorMsg = errorLine ? errorLine.replace('ML_ERROR:', '') : 'Unknown ML error';
            reject(new Error(errorMsg));
          }
        } catch (parseError) {
          reject(new Error(`ML result parsing error: ${parseError.message}\nOutput: ${output}`));
        }
      });
    });
  }

  async verifyFromDatabase(icText) {
    try {
      const icData = await ICData.findByPartNumber(icText);
      
      if (icData) {
        // Add verification record
        await icData.addVerification({
          scannedText: icText,
          verificationResult: 'authentic',
          confidence: 0.9,
          method: 'database_lookup'
        });

        return {
          found: true,
          icData: {
            partNumber: icData.partNumber,
            manufacturer: icData.manufacturer,
            description: icData.description,
            packageType: icData.packageType,
            specifications: icData.specifications
          }
        };
      } else {
        // Search for similar ICs
        const similarICs = await ICData.searchByText(icText, { limit: 5 });
        
        return {
          found: false,
          similar: similarICs.map(ic => ({
            partNumber: ic.partNumber,
            manufacturer: ic.manufacturer,
            similarity: this.calculateTextSimilarity(icText, ic.partNumber)
          }))
        };
      }
    } catch (error) {
      console.error('Database verification error:', error);
      return { found: false, error: error.message };
    }
  }

  async performIntelligentSearch(icText) {
    return new Promise((resolve, reject) => {
      const pythonScript = `
import sys
import os
sys.path.append('${path.dirname(this.intelligentSearchPath)}')

try:
    from intelligent_search import IntelligentICSearch
    searcher = IntelligentICSearch()
    result = searcher.process_ic_search_and_extraction('${icText}')
    print('SEARCH_RESULT:' + str(result))
except Exception as e:
    print('SEARCH_ERROR:' + str(e))
    import traceback
    traceback.print_exc()
`;

      const pythonProcess = spawn('python', ['-c', pythonScript], {
        stdio: 'pipe',
        env: { ...process.env, PYTHONPATH: path.dirname(this.intelligentSearchPath) }
      });

      let output = '';
      let errorOutput = '';

      pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });

      pythonProcess.on('close', (code) => {
        try {
          const lines = output.trim().split('\n');
          const resultLine = lines.find(line => line.startsWith('SEARCH_RESULT:'));
          
          if (resultLine) {
            const resultStr = resultLine.replace('SEARCH_RESULT:', '');
            // Note: Using eval here for simplicity, in production use proper JSON parsing
            const result = eval('(' + resultStr + ')');
            resolve(result);
          } else {
            const errorLine = lines.find(line => line.startsWith('SEARCH_ERROR:'));
            const errorMsg = errorLine ? errorLine.replace('SEARCH_ERROR:', '') : 'Unknown search error';
            reject(new Error(errorMsg + '\nOutput: ' + output + '\nError: ' + errorOutput));
          }
        } catch (parseError) {
          reject(new Error(`Search result parsing error: ${parseError.message}\nOutput: ${output}`));
        }
      });
    });
  }

  async performWebScraping(icText) {
    return new Promise((resolve, reject) => {
      const pythonScript = `
import sys
sys.path.append('${path.join(__dirname).replace(/\\/g, '/')}')

try:
    from web_scrapers import WebScrapingManager
    import json
    
    manager = WebScrapingManager()
    results = manager.search_all_sources('${icText}', max_results=5)
    
    output = {
        'status': 'success' if results else 'no_results',
        'results': [],
        'patterns': {}
    }
    
    for result in results:
        output['results'].append({
            'part_number': result.part_number,
            'manufacturer': result.manufacturer,
            'description': result.description,
            'datasheet_url': result.datasheet_url,
            'specifications': result.specifications or {},
            'source_url': result.source_url,
            'confidence_score': result.confidence_score
        })
    
    # Extract marking patterns
    if results:
        patterns = manager.extract_marking_patterns(results)
        output['patterns'] = patterns
    
    print('WEB_SCRAPING_RESULT:' + json.dumps(output))
except Exception as e:
    print('WEB_SCRAPING_ERROR:' + str(e))
    import traceback
    traceback.print_exc()
`;

      const pythonProcess = spawn('python', ['-c', pythonScript], {
        stdio: 'pipe',
        cwd: path.join(__dirname)
      });

      let output = '';
      let errorOutput = '';

      pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });

      pythonProcess.on('close', (code) => {
        try {
          const lines = output.trim().split('\n');
          const resultLine = lines.find(line => line.startsWith('WEB_SCRAPING_RESULT:'));
          
          if (resultLine) {
            const resultStr = resultLine.replace('WEB_SCRAPING_RESULT:', '');
            const result = JSON.parse(resultStr);
            resolve(result);
          } else {
            const errorLine = lines.find(line => line.startsWith('WEB_SCRAPING_ERROR:'));
            const errorMsg = errorLine ? errorLine.replace('WEB_SCRAPING_ERROR:', '') : 'Unknown web scraping error';
            reject(new Error(errorMsg + '\nOutput: ' + output + '\nError: ' + errorOutput));
          }
        } catch (parseError) {
          reject(new Error(`Web scraping result parsing error: ${parseError.message}\nOutput: ${output}`));
        }
      });
    });
  }

  async updateDatabaseFromScraping(icText, scrapingResult) {
    try {
      if (!scrapingResult.results || scrapingResult.results.length === 0) {
        return;
      }

      const bestResult = scrapingResult.results[0]; // Highest confidence result
      
      let icData = await ICData.findByPartNumber(icText);
      
      if (!icData) {
        // Create new IC record
        icData = new ICData({
          partNumber: icText.toUpperCase(),
          manufacturer: bestResult.manufacturer || 'Unknown',
          dataSource: 'web_scraping'
        });
      }

      // Update with scraping results
      icData.manufacturer = bestResult.manufacturer || icData.manufacturer;
      if (bestResult.description) {
        icData.specifications = icData.specifications || {};
        icData.specifications.description = bestResult.description;
      }
      
      // Add specifications from scraping
      if (bestResult.specifications) {
        icData.specifications = {
          ...icData.specifications,
          ...bestResult.specifications
        };
      }
      
      // Add document sources
      if (bestResult.datasheet_url) {
        icData.documentSources = icData.documentSources || [];
        icData.documentSources.push({
          type: 'datasheet',
          url: bestResult.datasheet_url,
          source: 'manufacturer_website',
          extractedAt: new Date()
        });
      }
      
      // Update marking information with patterns
      if (scrapingResult.patterns) {
        icData.markingInformation = icData.markingInformation || {};
        if (scrapingResult.patterns.standard_markings) {
          icData.markingInformation.standardMarkings = [
            ...(icData.markingInformation.standardMarkings || []),
            ...scrapingResult.patterns.standard_markings
          ];
        }
        if (scrapingResult.patterns.date_codes) {
          icData.markingInformation.dateCodes = [
            ...(icData.markingInformation.dateCodes || []),
            ...scrapingResult.patterns.date_codes
          ];
        }
      }
      
      // Update data quality
      icData.dataQuality = icData.dataQuality || {};
      icData.dataQuality.completeness = Math.max(icData.dataQuality.completeness || 0, bestResult.confidence_score || 0.7);
      icData.dataQuality.verified = true; // From manufacturer website
      icData.dataQuality.lastUpdated = new Date();
      icData.dataQuality.sources = [...(icData.dataQuality.sources || []), 'web_scraping'];

      await icData.save();
      console.log(`✅ Updated database record from web scraping for ${icText}`);
      return icData;
    } catch (error) {
      console.error('Error updating database from web scraping:', error);
      throw error;
    }
  }

  async updateDatabaseFromSearch(icText, searchResult) {
    try {
      let icData = await ICData.findByPartNumber(icText);
      
      if (!icData) {
        // Create new IC record
        icData = new ICData({
          partNumber: icText.toUpperCase(),
          manufacturer: 'Unknown',
          dataSource: 'internet_search'
        });
      }

      // Update with search results
      await icData.updateFromInternetSearch(searchResult);
      
      // Extract marking information from processed documents
      if (searchResult.processed_docs && searchResult.processed_docs.length > 0) {
        await icData.extractMarkingFromDocuments();
      }

      console.log(`✅ Updated database record for ${icText}`);
      return icData;
    } catch (error) {
      console.error('Error updating database from search:', error);
      throw error;
    }
  }

  async saveVerificationRecord(verificationResults) {
    try {
      const verification = new Verification({
        scannedText: verificationResults.icText,
        status: verificationResults.finalResult.status,
        confidence: verificationResults.confidence,
        isValid: verificationResults.finalResult.status === 'AUTHENTIC',
        verificationType: 'comprehensive',
        
        // Enhanced data
        verificationMethods: Object.keys(verificationResults.methods),
        methodResults: verificationResults.methods,
        recommendations: verificationResults.recommendations,
        
        // Match information if found
        matchedIC: verificationResults.finalResult.matched_ic ? {
          icModel: verificationResults.finalResult.matched_ic.ic_model || verificationResults.finalResult.matched_ic.partNumber,
          oemName: verificationResults.finalResult.matched_ic.oem_name || verificationResults.finalResult.matched_ic.manufacturer,
          packageType: verificationResults.finalResult.matched_ic.package_type || verificationResults.finalResult.matched_ic.packageType
        } : null,

        message: verificationResults.finalResult.message,
        processingTime: Date.now() - verificationResults.timestamp.getTime()
      });

      await verification.save();
      console.log('✅ Verification record saved');
      
      return verification;
    } catch (error) {
      console.error('Error saving verification record:', error);
      // Don't throw error here as verification itself succeeded
    }
  }

  calculateTextSimilarity(text1, text2) {
    // Simple similarity calculation
    const longer = text1.length > text2.length ? text1 : text2;
    const shorter = text1.length > text2.length ? text2 : text1;
    
    if (longer.length === 0) return 1.0;
    
    const editDistance = this.levenshteinDistance(longer, shorter);
    return (longer.length - editDistance) / longer.length;
  }

  levenshteinDistance(str1, str2) {
    const matrix = [];
    
    for (let i = 0; i <= str2.length; i++) {
      matrix[i] = [i];
    }
    
    for (let j = 0; j <= str1.length; j++) {
      matrix[0][j] = j;
    }
    
    for (let i = 1; i <= str2.length; i++) {
      for (let j = 1; j <= str1.length; j++) {
        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j] + 1
          );
        }
      }
    }
    
    return matrix[str2.length][str1.length];
  }

  /**
   * Background task to update IC data from internet
   */
  async updateICDataFromInternet() {
    console.log('🔄 Starting background IC data update...');
    
    try {
      const icsNeedingUpdate = await ICData.getNeedingUpdate();
      console.log(`Found ${icsNeedingUpdate.length} ICs needing update`);
      
      for (const ic of icsNeedingUpdate.slice(0, 10)) { // Process 10 at a time
        try {
          console.log(`Updating ${ic.partNumber}...`);
          const searchResult = await this.performIntelligentSearch(ic.partNumber);
          
          if (searchResult.status === 'success') {
            await ic.updateFromInternetSearch(searchResult);
            console.log(`✅ Updated ${ic.partNumber}`);
          }
        } catch (error) {
          console.log(`⚠️ Failed to update ${ic.partNumber}: ${error.message}`);
        }
        
        // Wait between requests to be respectful
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
      
      console.log('✅ Background update completed');
    } catch (error) {
      console.error('❌ Background update failed:', error);
    }
  }

  /**
   * Get system statistics
   */
  async getSystemStats() {
    try {
      const [icStats, verificationStats] = await Promise.all([
        ICData.getStatistics(),
        Verification.aggregate([
          {
            $group: {
              _id: null,
              totalVerifications: { $sum: 1 },
              authenticCount: {
                $sum: { $cond: [{ $eq: ['$status', 'AUTHENTIC'] }, 1, 0] }
              },
              averageConfidence: { $avg: '$confidence' },
              methodsUsed: { $addToSet: '$verificationMethods' }
            }
          }
        ])
      ]);

      return {
        icDatabase: icStats[0] || {},
        verifications: verificationStats[0] || {},
        timestamp: new Date()
      };
    } catch (error) {
      console.error('Error getting system stats:', error);
      return { error: error.message };
    }
  }
}

module.exports = IntegratedMLService;