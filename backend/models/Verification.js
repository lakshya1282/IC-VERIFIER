const mongoose = require('mongoose');

const verificationSchema = new mongoose.Schema({
  scannedText: {
    type: String,
    required: true,
    trim: true
  },
  extractedText: {
    type: String,
    trim: true
  },
  status: {
    type: String,
    enum: ['AUTHENTIC', 'FRAUD/UNKNOWN'],
    required: true
  },
  confidence: {
    type: Number,
    required: true,
    min: 0,
    max: 1
  },
  isValid: {
    type: Boolean,
    required: true
  },
  matchedIC: {
    icModel: String,
    oemName: String,
    packageType: String,
    markingText: String,
    datasheetUrl: String,
    releaseDate: String
  },
  possibleMatches: [{
    icModel: String,
    oemName: String,
    markingText: String,
    similarity: Number
  }],
  message: {
    type: String,
    required: true
  },
  verificationType: {
    type: String,
    enum: ['text', 'image'],
    required: true
  },
  imageData: {
    type: String  // Base64 encoded image (optional)
  },
  userAgent: String,
  ipAddress: String
}, {
  timestamps: true  // Automatically adds createdAt and updatedAt
});

// Index for faster queries
verificationSchema.index({ status: 1, createdAt: -1 });
verificationSchema.index({ 'matchedIC.oemName': 1 });

const Verification = mongoose.model('Verification', verificationSchema);

module.exports = Verification;
