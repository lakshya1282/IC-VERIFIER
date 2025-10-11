const axios = require('axios');
const fs = require('fs').promises;

const BASE_URL = 'http://localhost:3001/api';
const TEST_RESULTS_FILE = 'test_results.json';

// Test data for IC creation
const testICData = [
  {
    partNumber: 'TEST-IC-001',
    manufacturer: 'Test Corp',
    specifications: {
      category: 'Microcontroller',
      description: 'Test microcontroller for validation',
      package: 'DIP-8',
      pinCount: 8,
      operatingVoltage: '3.3V - 5V',
      operatingTemperature: '-40°C to +85°C'
    },
    markingInformation: {
      standardMarkings: ['TEST001', 'TC001'],
      lotCodes: ['L123456'],
      dateCodes: ['2024W01'],
      patterns: ['TEST\\d{3}']
    },
    documentSources: [{
      type: 'datasheet',
      url: 'http://example.com/test-ic-001.pdf',
      source: 'manufacturer',
      extractedAt: new Date()
    }]
  },
  {
    partNumber: 'TEST-IC-002',
    manufacturer: 'Another Corp',
    specifications: {
      category: 'Memory',
      description: 'Test EEPROM memory chip',
      package: 'SOIC-8',
      pinCount: 8
    },
    markingInformation: {
      standardMarkings: ['TEST002', 'AC002']
    }
  }
];

class ICEndpointTester {
  constructor() {
    this.testResults = [];
    this.createdICs = [];
  }

  async runTest(testName, testFunction) {
    console.log(`\n🧪 Running test: ${testName}`);
    try {
      const startTime = Date.now();
      const result = await testFunction();
      const duration = Date.now() - startTime;
      
      this.testResults.push({
        test: testName,
        status: 'PASS',
        duration: `${duration}ms`,
        result: result,
        timestamp: new Date().toISOString()
      });
      
      console.log(`✅ ${testName} - PASSED (${duration}ms)`);
      return result;
    } catch (error) {
      this.testResults.push({
        test: testName,
        status: 'FAIL',
        error: error.message,
        timestamp: new Date().toISOString()
      });
      
      console.log(`❌ ${testName} - FAILED: ${error.message}`);
      throw error;
    }
  }

  async testHealthCheck() {
    return await this.runTest('Health Check (Enhanced)', async () => {
      const response = await axios.get(`${BASE_URL}/health`);
      
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }
      
      const data = response.data;
      if (!data.enhanced_features || !data.enhanced_features.intelligent_search) {
        throw new Error('Enhanced features not found in health check');
      }
      
      return data;
    });
  }

  async testICStats() {
    return await this.runTest('IC Statistics (Enhanced)', async () => {
      const response = await axios.get(`${BASE_URL}/ic-stats`);
      
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }
      
      const data = response.data;
      if (!data.enhanced_features) {
        throw new Error('Enhanced features not found in IC stats');
      }
      
      return data;
    });
  }

  async testCreateICData() {
    return await this.runTest('Create IC Data', async () => {
      const icData = testICData[0];
      const response = await axios.post(`${BASE_URL}/ic-data`, icData);
      
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }
      
      const data = response.data;
      if (data.operation !== 'create') {
        throw new Error('Expected create operation');
      }
      
      this.createdICs.push(icData.partNumber);
      return data;
    });
  }

  async testUpdateICData() {
    return await this.runTest('Update IC Data', async () => {
      const icData = { ...testICData[0] };
      icData.specifications.description = 'Updated test microcontroller';
      
      const response = await axios.post(`${BASE_URL}/ic-data`, icData);
      
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }
      
      const data = response.data;
      if (data.operation !== 'update') {
        throw new Error('Expected update operation');
      }
      
      return data;
    });
  }

  async testGetICDetails() {
    return await this.runTest('Get IC Details', async () => {
      const partNumber = testICData[0].partNumber;
      const response = await axios.get(`${BASE_URL}/ic-details/${partNumber}`);
      
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }
      
      const data = response.data;
      if (!data.ic_data || !data.marking_information) {
        throw new Error('IC details structure invalid');
      }
      
      return data;
    });
  }

  async testICDatabase() {
    return await this.runTest('Get IC Database', async () => {
      const response = await axios.get(`${BASE_URL}/ic-database?limit=10`);
      
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }
      
      const data = response.data;
      if (!Array.isArray(data.ic_data) || !data.intelligent_search_enabled) {
        throw new Error('IC database structure invalid');
      }
      
      return data;
    });
  }

  async testSearchICDatabase() {
    return await this.runTest('Search IC Database', async () => {
      const response = await axios.get(`${BASE_URL}/ic-database?search=microcontroller&limit=5`);
      
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }
      
      const data = response.data;
      if (!Array.isArray(data.ic_data) || data.search_query !== 'microcontroller') {
        throw new Error('Search results structure invalid');
      }
      
      return data;
    });
  }

  async testPopularICs() {
    return await this.runTest('Get Popular ICs', async () => {
      const response = await axios.get(`${BASE_URL}/popular-ics?limit=5`);
      
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }
      
      const data = response.data;
      if (!Array.isArray(data.popular_ics)) {
        throw new Error('Popular ICs structure invalid');
      }
      
      return data;
    });
  }

  async testBatchCreateICData() {
    return await this.runTest('Batch Create IC Data', async () => {
      const response = await axios.post(`${BASE_URL}/ic-data/batch`, {
        operation: 'create',
        ic_data: testICData.slice(1) // Create second test IC
      });
      
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }
      
      const data = response.data;
      if (data.successful < 1) {
        throw new Error('Batch create failed');
      }
      
      this.createdICs.push(testICData[1].partNumber);
      return data;
    });
  }

  async testUpdateICDataFromInternet() {
    return await this.runTest('Update IC Data from Internet', async () => {
      const response = await axios.post(`${BASE_URL}/update-ic-data`, {
        ic_part_number: '555'
      });
      
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }
      
      const data = response.data;
      if (!data.message) {
        throw new Error('Internet update response invalid');
      }
      
      return data;
    });
  }

  async testIntelligentSearch() {
    return await this.runTest('Intelligent Search', async () => {
      const response = await axios.post(`${BASE_URL}/intelligent-search`, {
        query: 'LM555 timer IC datasheet'
      });
      
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }
      
      const data = response.data;
      if (!data.search_results) {
        throw new Error('Intelligent search results invalid');
      }
      
      return data;
    });
  }

  async testDataQuality() {
    return await this.runTest('Data Quality Assessment', async () => {
      const response = await axios.get(`${BASE_URL}/data-quality`);
      
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }
      
      const data = response.data;
      if (!data.overall_quality || !data.recommendations) {
        throw new Error('Data quality response structure invalid');
      }
      
      return data;
    });
  }

  async testBatchUpdateQuality() {
    return await this.runTest('Batch Update Quality', async () => {
      const response = await axios.post(`${BASE_URL}/ic-data/batch`, {
        operation: 'update_quality',
        part_numbers: this.createdICs
      });
      
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }
      
      const data = response.data;
      if (data.successful < 1) {
        throw new Error('Batch quality update failed');
      }
      
      return data;
    });
  }

  async testComprehensiveVerification() {
    return await this.runTest('Comprehensive Verification (Text)', async () => {
      const response = await axios.post(`${BASE_URL}/verify-comprehensive`, {
        marking_text: 'TEST001'
      });
      
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }
      
      const data = response.data;
      if (!data.verification_results || !data.confidence_score) {
        throw new Error('Comprehensive verification response invalid');
      }
      
      return data;
    });
  }

  async testSoftDelete() {
    return await this.runTest('Soft Delete IC Data', async () => {
      const partNumber = testICData[1].partNumber;
      const response = await axios.delete(`${BASE_URL}/ic-data/${partNumber}?soft_delete=true`);
      
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }
      
      const data = response.data;
      if (data.operation !== 'soft_delete') {
        throw new Error('Expected soft delete operation');
      }
      
      return data;
    });
  }

  async testBatchDelete() {
    return await this.runTest('Batch Delete IC Data', async () => {
      const response = await axios.post(`${BASE_URL}/ic-data/batch`, {
        operation: 'delete',
        part_numbers: [testICData[0].partNumber]
      });
      
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }
      
      const data = response.data;
      if (data.successful < 1) {
        throw new Error('Batch delete failed');
      }
      
      return data;
    });
  }

  async cleanup() {
    console.log('\n🧹 Cleaning up test data...');
    
    for (const partNumber of this.createdICs) {
      try {
        await axios.delete(`${BASE_URL}/ic-data/${partNumber}?soft_delete=false`);
        console.log(`  ✅ Cleaned up ${partNumber}`);
      } catch (error) {
        console.log(`  ⚠️ Failed to cleanup ${partNumber}: ${error.message}`);
      }
    }
  }

  async generateReport() {
    const summary = {
      total_tests: this.testResults.length,
      passed: this.testResults.filter(t => t.status === 'PASS').length,
      failed: this.testResults.filter(t => t.status === 'FAIL').length,
      test_run_timestamp: new Date().toISOString(),
      results: this.testResults
    };

    summary.success_rate = `${Math.round((summary.passed / summary.total_tests) * 100)}%`;

    await fs.writeFile(TEST_RESULTS_FILE, JSON.stringify(summary, null, 2));
    
    console.log('\n📊 Test Summary:');
    console.log(`   Total Tests: ${summary.total_tests}`);
    console.log(`   Passed: ${summary.passed}`);
    console.log(`   Failed: ${summary.failed}`);
    console.log(`   Success Rate: ${summary.success_rate}`);
    console.log(`   Report saved to: ${TEST_RESULTS_FILE}`);

    return summary;
  }

  async runAllTests() {
    console.log('🚀 Starting IC Data Management Endpoint Tests...');
    console.log(`Testing against: ${BASE_URL}`);
    
    try {
      // Basic functionality tests
      await this.testHealthCheck();
      await this.testICStats();
      
      // CRUD operations
      await this.testCreateICData();
      await this.testUpdateICData();
      await this.testGetICDetails();
      
      // Search and retrieval
      await this.testICDatabase();
      await this.testSearchICDatabase();
      await this.testPopularICs();
      
      // Batch operations
      await this.testBatchCreateICData();
      await this.testBatchUpdateQuality();
      
      // Advanced features
      await this.testUpdateICDataFromInternet();
      await this.testIntelligentSearch();
      await this.testDataQuality();
      await this.testComprehensiveVerification();
      
      // Deletion tests
      await this.testSoftDelete();
      await this.testBatchDelete();
      
      console.log('\n✅ All tests completed successfully!');
      
    } catch (error) {
      console.log('\n❌ Test suite failed with errors');
    } finally {
      await this.cleanup();
      await this.generateReport();
    }
  }
}

// Main execution
if (require.main === module) {
  const tester = new ICEndpointTester();
  tester.runAllTests().catch(console.error);
}

module.exports = ICEndpointTester;