#!/usr/bin/env node

const axios = require('axios');

const BASE_URL = 'http://localhost:3001/api';

async function quickTest() {
  console.log('🚀 Quick Test of New IC Data Management Endpoints');
  console.log('='.repeat(60));
  
  try {
    // Test 1: Enhanced Health Check
    console.log('\n1️⃣ Testing Enhanced Health Check...');
    const health = await axios.get(`${BASE_URL}/health`);
    console.log(`   Status: ${health.status}`);
    console.log(`   Enhanced Features: ${JSON.stringify(health.data.enhanced_features, null, 2)}`);
    
    // Test 2: Enhanced IC Stats
    console.log('\n2️⃣ Testing Enhanced IC Statistics...');
    const stats = await axios.get(`${BASE_URL}/ic-stats`);
    console.log(`   Status: ${stats.status}`);
    console.log(`   Enhanced Features: ${JSON.stringify(stats.data.enhanced_features, null, 2)}`);
    
    // Test 3: IC Database with Search
    console.log('\n3️⃣ Testing IC Database...');
    const database = await axios.get(`${BASE_URL}/ic-database?limit=5`);
    console.log(`   Status: ${database.status}`);
    console.log(`   Total Records: ${database.data.total_count}`);
    console.log(`   Intelligent Search: ${database.data.intelligent_search_enabled}`);
    
    // Test 4: Data Quality Assessment
    console.log('\n4️⃣ Testing Data Quality Assessment...');
    const quality = await axios.get(`${BASE_URL}/data-quality`);
    console.log(`   Status: ${quality.status}`);
    console.log(`   Overall Quality: ${JSON.stringify(quality.data.overall_quality, null, 2)}`);
    
    // Test 5: Create Test IC Data
    console.log('\n5️⃣ Testing Create IC Data...');
    const testIC = {
      partNumber: 'QUICK-TEST-001',
      manufacturer: 'Test Manufacturing',
      specifications: {
        category: 'Microcontroller',
        description: 'Quick test IC for endpoint validation',
        package: 'DIP-8',
        pinCount: 8
      },
      markingInformation: {
        standardMarkings: ['QT001', 'TEST001']
      }
    };
    
    const createResult = await axios.post(`${BASE_URL}/ic-data`, testIC);
    console.log(`   Status: ${createResult.status}`);
    console.log(`   Operation: ${createResult.data.operation}`);
    console.log(`   Part Number: ${createResult.data.ic_data.partNumber}`);
    
    // Test 6: Get IC Details
    console.log('\n6️⃣ Testing Get IC Details...');
    const details = await axios.get(`${BASE_URL}/ic-details/${testIC.partNumber}`);
    console.log(`   Status: ${details.status}`);
    console.log(`   Found IC: ${details.data.ic_data.partNumber}`);
    console.log(`   Manufacturer: ${details.data.ic_data.manufacturer}`);
    
    // Test 7: Update IC Data from Internet (Test with known IC)
    console.log('\n7️⃣ Testing Update IC Data from Internet...');
    const internetUpdate = await axios.post(`${BASE_URL}/update-ic-data`, {
      ic_part_number: '555'
    });
    console.log(`   Status: ${internetUpdate.status}`);
    console.log(`   Message: ${internetUpdate.data.message}`);
    
    // Test 8: Intelligent Search
    console.log('\n8️⃣ Testing Intelligent Search...');
    const intelligentSearch = await axios.post(`${BASE_URL}/intelligent-search`, {
      query: 'LM555 timer IC datasheet'
    });
    console.log(`   Status: ${intelligentSearch.status}`);
    console.log(`   Search performed: ${intelligentSearch.data.search_performed}`);
    
    // Test 9: Comprehensive Verification
    console.log('\n9️⃣ Testing Comprehensive Verification...');
    const verification = await axios.post(`${BASE_URL}/verify-comprehensive`, {
      marking_text: 'QT001'
    });
    console.log(`   Status: ${verification.status}`);
    console.log(`   Confidence: ${verification.data.confidence_score}%`);
    console.log(`   Result: ${verification.data.verification_results.is_authentic ? 'Authentic' : 'Not Authentic'}`);
    
    // Test 10: Cleanup Test IC
    console.log('\n🧹 Cleaning up test data...');
    const deleteResult = await axios.delete(`${BASE_URL}/ic-data/${testIC.partNumber}?soft_delete=false`);
    console.log(`   Cleanup Status: ${deleteResult.status}`);
    console.log(`   Operation: ${deleteResult.data.operation}`);
    
    console.log('\n✅ All quick tests completed successfully!');
    console.log('='.repeat(60));
    
  } catch (error) {
    console.error('\n❌ Quick test failed:', error.message);
    if (error.response) {
      console.error('   Response Status:', error.response.status);
      console.error('   Response Data:', error.response.data);
    }
  }
}

// Run the quick test
if (require.main === module) {
  quickTest().catch(console.error);
}

module.exports = quickTest;