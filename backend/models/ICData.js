const mongoose = require('mongoose');

// Enhanced IC Data model for dynamic internet-sourced information
const ICDataSchema = new mongoose.Schema({
  // Basic IC Information
  partNumber: {
    type: String,
    required: true,
    index: true,
    uppercase: true,
    trim: true
  },
  manufacturer: {
    type: String,
    required: true,
    index: true
  },
  description: String,
  
  // Package Information
  packageType: {
    type: String,
    index: true
  },
  pinCount: Number,
  packageSize: {
    width: Number,
    height: Number,
    thickness: Number,
    unit: {
      type: String,
      default: 'mm'
    }
  },
  
  // Marking Information (extracted from documents)
  markingInformation: {
    standardMarking: String,  // How it should appear on genuine ICs
    markingCodes: [String],   // Alternative marking patterns
    dateCodePattern: String,  // How date codes appear
    lotCodePattern: String,   // Lot code patterns
    assemblyCodePattern: String,
    topMarkLayout: String,    // Description of top marking layout
    markingFont: String,      // Font characteristics if specified
    markingMethod: {
      type: String,
      enum: ['laser', 'inkjet', 'embossed', 'etched', 'silk_screen']
    }
  },
  
  // Technical Specifications
  specifications: {
    operatingVoltage: {
      min: Number,
      max: Number,
      typical: Number,
      unit: String
    },
    operatingTemperature: {
      min: Number,
      max: Number,
      unit: {
        type: String,
        default: 'C'
      }
    },
    frequency: {
      value: Number,
      unit: String
    },
    power: {
      value: Number,
      unit: String
    },
    category: {
      type: String,
      enum: ['microcontroller', 'processor', 'memory', 'analog', 'digital', 'power', 'interface', 'sensor', 'other']
    }
  },
  
  // Document Sources
  documentSources: [{
    title: String,
    url: String,
    pdfUrl: String,
    source: String,  // 'manufacturer', 'datasheet_site', 'academic', etc.
    confidenceScore: Number,
    downloadDate: Date,
    localPath: String,  // Local file path if downloaded
    extractedText: String,  // Key extracted text
    verified: {
      type: Boolean,
      default: false
    }
  }],
  
  // Verification History
  verificationHistory: [{
    scannedText: String,
    verificationResult: {
      type: String,
      enum: ['authentic', 'fraud', 'unknown']
    },
    confidence: Number,
    timestamp: {
      type: Date,
      default: Date.now
    },
    method: {
      type: String,
      enum: ['ml_model', 'deep_learning', 'manual', 'internet_search']
    },
    userAgent: String,
    ipAddress: String
  }],
  
  // Search and Update Information
  searchMetadata: {
    lastSearchDate: Date,
    searchQueries: [String],
    documentsFound: Number,
    documentsProcessed: Number,
    internetSearchEnabled: {
      type: Boolean,
      default: true
    },
    nextScheduledUpdate: Date
  },
  
  // Status and Quality
  dataQuality: {
    completeness: Number,  // 0-100 percentage
    reliability: Number,   // 0-100 based on source quality
    lastVerified: Date,
    verificationStatus: {
      type: String,
      enum: ['verified', 'pending', 'disputed', 'obsolete'],
      default: 'pending'
    }
  },
  
  // Fraud Detection Patterns
  fraudPatterns: [{
    description: String,
    pattern: String,       // Regex or description
    severity: {
      type: String,
      enum: ['low', 'medium', 'high', 'critical']
    },
    reportedDate: Date,
    reportedBy: String
  }],
  
  // Related ICs (family, variants, etc.)
  relatedICs: [{
    partNumber: String,
    relationship: {
      type: String,
      enum: ['variant', 'family', 'replacement', 'compatible']
    },
    notes: String
  }],
  
  // Timestamps and Metadata
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  },
  lastInternetUpdate: Date,
  dataSource: {
    type: String,
    enum: ['manual', 'csv_import', 'internet_search', 'ml_extraction'],
    default: 'manual'
  },
  isActive: {
    type: Boolean,
    default: true
  },
  
  // Indexing for search optimization
  searchTags: [String],  // For faster searching
  popularity: {
    type: Number,
    default: 0
  }  // Based on verification frequency
});

// Indexes for performance
ICDataSchema.index({ partNumber: 1, manufacturer: 1 }, { unique: true });
ICDataSchema.index({ 'specifications.category': 1 });
ICDataSchema.index({ 'searchMetadata.lastSearchDate': 1 });
ICDataSchema.index({ 'dataQuality.verificationStatus': 1 });
ICDataSchema.index({ popularity: -1 });
ICDataSchema.index({ searchTags: 1 });

// Middleware to update timestamps
ICDataSchema.pre('save', function(next) {
  this.updatedAt = new Date();
  if (this.isNew) {
    this.createdAt = new Date();
  }
  next();
});

// Methods
ICDataSchema.methods.addVerification = function(verificationData) {
  this.verificationHistory.push(verificationData);
  this.popularity += 1;
  return this.save();
};

ICDataSchema.methods.updateFromInternetSearch = function(searchResults) {
  this.documentSources = searchResults.documents || [];
  this.searchMetadata.lastSearchDate = new Date();
  this.searchMetadata.documentsFound = searchResults.found_documents || 0;
  this.searchMetadata.documentsProcessed = searchResults.processed_documents || 0;
  this.lastInternetUpdate = new Date();
  this.dataSource = 'internet_search';
  
  // Update quality score based on sources
  if (this.documentSources.length > 0) {
    const avgConfidence = this.documentSources.reduce((sum, doc) => sum + (doc.confidenceScore || 0), 0) / this.documentSources.length;
    this.dataQuality.reliability = Math.min(100, avgConfidence * 100);
  }
  
  return this.save();
};

ICDataSchema.methods.extractMarkingFromDocuments = function() {
  const markings = {
    standardMarking: this.partNumber,
    markingCodes: [],
    extractedPatterns: []
  };
  
  this.documentSources.forEach(doc => {
    if (doc.extractedText) {
      // Extract marking patterns from text
      const patterns = this.extractMarkingPatterns(doc.extractedText);
      markings.markingCodes.push(...patterns);
    }
  });
  
  this.markingInformation = { ...this.markingInformation, ...markings };
  return this.save();
};

ICDataSchema.methods.extractMarkingPatterns = function(text) {
  const patterns = [];
  
  // Common IC marking patterns
  const markingRegexes = [
    /([A-Z]{2,4}\d{3,6}[A-Z]?)/g,  // Standard IC patterns
    /(\d{4}[A-Z]\d{2})/g,          // Date codes
    /([A-Z]\d{3}[A-Z])/g           // Lot codes
  ];
  
  markingRegexes.forEach(regex => {
    const matches = text.match(regex);
    if (matches) {
      patterns.push(...matches);
    }
  });
  
  return [...new Set(patterns)]; // Remove duplicates
};

// Static methods
ICDataSchema.statics.findByPartNumber = function(partNumber) {
  return this.findOne({ partNumber: partNumber.toUpperCase() });
};

ICDataSchema.statics.searchByText = function(searchText, options = {}) {
  const query = {
    $or: [
      { partNumber: new RegExp(searchText, 'i') },
      { manufacturer: new RegExp(searchText, 'i') },
      { description: new RegExp(searchText, 'i') },
      { searchTags: new RegExp(searchText, 'i') }
    ]
  };
  
  return this.find(query)
    .limit(options.limit || 20)
    .sort({ popularity: -1, updatedAt: -1 });
};

ICDataSchema.statics.getNeedingUpdate = function() {
  const weekAgo = new Date();
  weekAgo.setDate(weekAgo.getDate() - 7);
  
  return this.find({
    $or: [
      { 'searchMetadata.lastSearchDate': { $lt: weekAgo } },
      { 'searchMetadata.lastSearchDate': { $exists: false } }
    ],
    'searchMetadata.internetSearchEnabled': true,
    isActive: true
  }).limit(50); // Process in batches
};

ICDataSchema.statics.getPopularICs = function(limit = 10) {
  return this.find({ isActive: true })
    .sort({ popularity: -1 })
    .limit(limit)
    .select('partNumber manufacturer popularity verificationHistory');
};

ICDataSchema.statics.getStatistics = function() {
  return this.aggregate([
    {
      $group: {
        _id: null,
        totalICs: { $sum: 1 },
        verifiedICs: {
          $sum: {
            $cond: [{ $eq: ['$dataQuality.verificationStatus', 'verified'] }, 1, 0]
          }
        },
        avgReliability: { $avg: '$dataQuality.reliability' },
        manufacturerCount: { $addToSet: '$manufacturer' }
      }
    },
    {
      $project: {
        totalICs: 1,
        verifiedICs: 1,
        avgReliability: 1,
        uniqueManufacturers: { $size: '$manufacturerCount' }
      }
    }
  ]);
};

// Virtual for full search text
ICDataSchema.virtual('searchableText').get(function() {
  return `${this.partNumber} ${this.manufacturer} ${this.description || ''} ${this.searchTags?.join(' ') || ''}`;
});

// Ensure virtual fields are serialized
ICDataSchema.set('toJSON', { virtuals: true });
ICDataSchema.set('toObject', { virtuals: true });

module.exports = mongoose.model('ICData', ICDataSchema);