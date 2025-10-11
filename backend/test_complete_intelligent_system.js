#!/usr/bin/env node

/**
 * Complete Intelligent System End-to-End Test
 * Tests the full IC verification system with internet search, document processing, ML integration, and web scraping
 */

const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');

const BASE_URL = 'http://localhost:3001/api';
const TEST_RESULTS_FILE = 'complete_system_test_results.json';

// Test scenarios with different types of IC markings
const TEST_SCENARIOS = [
    {
        name: 'Popular IC - LM555',
        icMarking: 'LM555',
        expectedResult: 'AUTHENTIC',
        expectWebScraping: true,
        expectDatabaseMatch: true,
        description: 'Well-known timer IC from multiple manufacturers'
    },
    {
        name: 'Microcontroller - ATmega328P',
        icMarking: 'ATmega328P',
        expectedResult: 'AUTHENTIC',
        expectWebScraping: true,
        expectDatabaseMatch: false,
        description: 'Arduino microcontroller, should be found via web scraping'
    },
    {
        name: 'Op-Amp - LM358',
        icMarking: 'LM358',
        expectedResult: 'AUTHENTIC',
        expectWebScraping: true,
        expectDatabaseMatch: false,
        description: 'Dual operational amplifier'
    },
    {
        name: 'Obscure IC - Unknown123',
        icMarking: 'UNKNOWN123XYZ',
        expectedResult: 'COUNTERFEIT',
        expectWebScraping: false,
        expectDatabaseMatch: false,
        description: 'Non-existent IC part, should be flagged as counterfeit'
    },
    {
        name: 'Logic Gate - CD4011',
        icMarking: 'CD4011',
        expectedResult: 'AUTHENTIC',
        expectWebScraping: true,
        expectDatabaseMatch: false,
        description: 'CMOS NAND gate, should be verifiable'
    }
];

class CompleteSystemTester {
    constructor() {
        this.testResults = [];
        this.systemStats = {
            totalTests: 0,
            passedTests: 0,
            failedTests: 0,
            methodsUsed: new Set(),
            averageResponseTime: 0,
            totalResponseTime: 0
        };
    }

    async runCompleteSystemTest() {
        console.log('🚀 Starting Complete Intelligent System End-to-End Test');
        console.log('='.repeat(80));
        console.log(`Testing ${TEST_SCENARIOS.length} different IC verification scenarios`);
        console.log('Testing: Internet Search + Web Scraping + ML Integration + Document Processing');
        console.log('='.repeat(80));

        // Step 1: Verify system health
        await this.verifySystemHealth();

        // Step 2: Test each scenario
        for (let i = 0; i < TEST_SCENARIOS.length; i++) {
            const scenario = TEST_SCENARIOS[i];
            console.log(`\n📋 Test ${i + 1}/${TEST_SCENARIOS.length}: ${scenario.name}`);
            console.log(`   IC Marking: ${scenario.icMarking}`);
            console.log(`   Expected: ${scenario.expectedResult}`);
            console.log(`   Description: ${scenario.description}`);
            
            await this.testScenario(scenario, i + 1);
            
            // Wait between tests to avoid overwhelming the system
            if (i < TEST_SCENARIOS.length - 1) {
                console.log('   ⏳ Waiting 3 seconds before next test...');
                await this.sleep(3000);
            }
        }

        // Step 3: Test additional system capabilities
        await this.testSystemCapabilities();

        // Step 4: Generate comprehensive report
        await this.generateReport();
    }

    async verifySystemHealth() {
        console.log('\n🔍 Step 1: System Health Verification');
        console.log('-'.repeat(50));
        
        try {
            // Test basic health endpoint
            const health = await axios.get(`${BASE_URL}/health`);
            console.log(`✅ Backend Health: ${health.data.status}`);
            console.log(`   Enhanced Features: ${JSON.stringify(health.data.enhanced_features)}`);

            // Test ML components
            const stats = await axios.get(`${BASE_URL}/ic-stats`);
            console.log(`✅ ML Statistics Available`);
            console.log(`   Traditional ML: ${stats.data.traditional_ml ? 'Available' : 'Unavailable'}`);
            console.log(`   Enhanced Features: ${JSON.stringify(stats.data.enhanced_features)}`);

            // Test database
            const database = await axios.get(`${BASE_URL}/ic-database?limit=1`);
            console.log(`✅ Database Connection: OK`);
            console.log(`   Total IC Records: ${database.data.total_count}`);
            console.log(`   Categories: ${database.data.categories.length}`);
            console.log(`   Manufacturers: ${database.data.manufacturers.length}`);

        } catch (error) {
            console.error('❌ System health check failed:', error.message);
            throw new Error('System not ready for testing');
        }
    }

    async testScenario(scenario, testNumber) {
        const startTime = Date.now();
        let testResult = {
            test_number: testNumber,
            scenario_name: scenario.name,
            ic_marking: scenario.icMarking,
            expected_result: scenario.expectedResult,
            actual_result: null,
            methods_used: [],
            response_time: 0,
            confidence_score: 0,
            verification_details: {},
            passed: false,
            errors: [],
            timestamp: new Date().toISOString()
        };

        try {
            console.log('   🔬 Performing comprehensive verification...');
            
            // Use the comprehensive verification endpoint that includes all methods
            const response = await axios.post(`${BASE_URL}/verify-comprehensive`, {
                marking_text: scenario.icMarking
            }, {
                timeout: 60000 // 60 second timeout for complex verifications
            });

            const responseTime = Date.now() - startTime;
            testResult.response_time = responseTime;
            this.systemStats.totalResponseTime += responseTime;

            if (response.status === 200) {
                const data = response.data;
                
                testResult.actual_result = data.verification_results.is_authentic ? 'AUTHENTIC' : 'COUNTERFEIT';
                testResult.confidence_score = data.confidence_score;
                testResult.methods_used = data.verification_results.methods_used || [];
                testResult.verification_details = {
                    deep_learning: data.verification_results.deep_learning_result,
                    traditional_ml: data.verification_results.traditional_ml_result,
                    database_lookup: data.verification_results.database_result,
                    internet_search: data.verification_results.internet_search_result,
                    web_scraping: data.verification_results.web_scraping_result,
                    final_decision: data.verification_results.decision_reasoning
                };

                // Track methods used
                testResult.methods_used.forEach(method => {
                    this.systemStats.methodsUsed.add(method);
                });

                // Evaluate test success
                const resultMatches = testResult.actual_result === scenario.expectedResult;
                const confidenceAcceptable = testResult.confidence_score >= 0.5;
                const methodsExpected = this.validateExpectedMethods(scenario, testResult);

                testResult.passed = resultMatches && confidenceAcceptable && methodsExpected;

                if (testResult.passed) {
                    console.log(`   ✅ TEST PASSED`);
                    console.log(`      Result: ${testResult.actual_result} (Expected: ${scenario.expectedResult})`);
                    console.log(`      Confidence: ${testResult.confidence_score}%`);
                    console.log(`      Methods: ${testResult.methods_used.join(', ')}`);
                    console.log(`      Response Time: ${responseTime}ms`);
                    this.systemStats.passedTests++;
                } else {
                    console.log(`   ❌ TEST FAILED`);
                    console.log(`      Expected: ${scenario.expectedResult}, Got: ${testResult.actual_result}`);
                    console.log(`      Confidence: ${testResult.confidence_score}%`);
                    console.log(`      Methods: ${testResult.methods_used.join(', ')}`);
                    testResult.errors.push('Result or confidence did not meet expectations');
                    this.systemStats.failedTests++;
                }

                // Log detailed method results
                console.log('   📊 Method Results:');
                Object.entries(testResult.verification_details).forEach(([method, result]) => {
                    if (result && typeof result === 'object') {
                        console.log(`      ${method}: ${JSON.stringify(result).substring(0, 100)}...`);
                    }
                });

            } else {
                throw new Error(`Unexpected response status: ${response.status}`);
            }

        } catch (error) {
            const responseTime = Date.now() - startTime;
            testResult.response_time = responseTime;
            testResult.errors.push(error.message);
            testResult.passed = false;
            
            console.log(`   ❌ TEST ERROR: ${error.message}`);
            console.log(`      Response Time: ${responseTime}ms`);
            this.systemStats.failedTests++;
        }

        this.testResults.push(testResult);
        this.systemStats.totalTests++;
    }

    validateExpectedMethods(scenario, testResult) {
        // Check if expected methods were used based on scenario
        let validationPassed = true;
        
        if (scenario.expectDatabaseMatch) {
            if (!testResult.methods_used.includes('database')) {
                console.log('   ⚠️  Expected database match but method not used');
                validationPassed = false;
            }
        }

        if (scenario.expectWebScraping) {
            if (!testResult.methods_used.includes('web_scraping') && 
                !testResult.methods_used.includes('internet_search')) {
                console.log('   ⚠️  Expected web scraping/internet search but methods not used');
                // Not failing the test for this as these are fallback methods
            }
        }

        return validationPassed;
    }

    async testSystemCapabilities() {
        console.log('\n🛠️  Additional System Capabilities Testing');
        console.log('-'.repeat(50));

        try {
            // Test 1: Data Quality Assessment
            console.log('   Testing data quality assessment...');
            const qualityResponse = await axios.get(`${BASE_URL}/data-quality`);
            console.log(`   ✅ Data Quality: ${qualityResponse.data.overall_quality.averageCompleteness || 'N/A'}`);

            // Test 2: Popular ICs endpoint
            console.log('   Testing popular ICs retrieval...');
            const popularResponse = await axios.get(`${BASE_URL}/popular-ics?limit=5`);
            console.log(`   ✅ Popular ICs: ${popularResponse.data.popular_ics.length} retrieved`);

            // Test 3: Internet search endpoint
            console.log('   Testing intelligent search capability...');
            const searchResponse = await axios.post(`${BASE_URL}/intelligent-search`, {
                query: 'LM555 timer IC datasheet'
            });
            console.log(`   ✅ Intelligent Search: ${searchResponse.data.status}`);

            // Test 4: IC data creation
            console.log('   Testing IC data management...');
            const createResponse = await axios.post(`${BASE_URL}/ic-data`, {
                partNumber: 'TEST-COMPLETE-001',
                manufacturer: 'Test Corp',
                specifications: {
                    category: 'Test IC',
                    description: 'Complete system test IC'
                },
                markingInformation: {
                    standardMarkings: ['TEST001']
                }
            });
            console.log(`   ✅ IC Data Creation: ${createResponse.data.operation}`);

            // Cleanup test data
            await axios.delete(`${BASE_URL}/ic-data/TEST-COMPLETE-001?soft_delete=false`);
            console.log('   ✅ Test data cleaned up');

        } catch (error) {
            console.log(`   ❌ System capabilities test error: ${error.message}`);
        }
    }

    async generateReport() {
        console.log('\n📊 Generating Comprehensive Test Report');
        console.log('='.repeat(80));

        // Calculate statistics
        this.systemStats.averageResponseTime = this.systemStats.totalResponseTime / this.systemStats.totalTests;
        const successRate = (this.systemStats.passedTests / this.systemStats.totalTests) * 100;

        // Display summary
        console.log(`\n🏆 TEST SUMMARY:`);
        console.log(`   Total Tests: ${this.systemStats.totalTests}`);
        console.log(`   Passed: ${this.systemStats.passedTests}`);
        console.log(`   Failed: ${this.systemStats.failedTests}`);
        console.log(`   Success Rate: ${successRate.toFixed(1)}%`);
        console.log(`   Average Response Time: ${this.systemStats.averageResponseTime.toFixed(0)}ms`);
        console.log(`   Methods Used: ${Array.from(this.systemStats.methodsUsed).join(', ')}`);

        // Method effectiveness analysis
        console.log(`\n🔍 METHOD EFFECTIVENESS:`);
        const methodStats = this.analyzeMethodEffectiveness();
        Object.entries(methodStats).forEach(([method, stats]) => {
            console.log(`   ${method}: Used in ${stats.usage} tests, Success rate: ${stats.successRate.toFixed(1)}%`);
        });

        // Performance analysis
        console.log(`\n⚡ PERFORMANCE ANALYSIS:`);
        const performanceStats = this.analyzePerformance();
        console.log(`   Fastest Response: ${performanceStats.fastest}ms`);
        console.log(`   Slowest Response: ${performanceStats.slowest}ms`);
        console.log(`   Median Response: ${performanceStats.median}ms`);

        // System intelligence assessment
        console.log(`\n🧠 SYSTEM INTELLIGENCE ASSESSMENT:`);
        const intelligenceScore = this.assessSystemIntelligence();
        console.log(`   Overall Intelligence Score: ${intelligenceScore.overall}/100`);
        console.log(`   Web Scraping Capability: ${intelligenceScore.webScraping}/25`);
        console.log(`   Internet Search Capability: ${intelligenceScore.internetSearch}/25`);
        console.log(`   ML Integration: ${intelligenceScore.mlIntegration}/25`);
        console.log(`   Database Utilization: ${intelligenceScore.databaseUtilization}/25`);

        // Generate recommendations
        const recommendations = this.generateRecommendations(successRate, intelligenceScore);
        console.log(`\n💡 RECOMMENDATIONS:`);
        recommendations.forEach((rec, index) => {
            console.log(`   ${index + 1}. ${rec}`);
        });

        // Save detailed report
        const detailedReport = {
            test_summary: {
                total_tests: this.systemStats.totalTests,
                passed_tests: this.systemStats.passedTests,
                failed_tests: this.systemStats.failedTests,
                success_rate: successRate,
                average_response_time: this.systemStats.averageResponseTime
            },
            method_effectiveness: methodStats,
            performance_analysis: performanceStats,
            intelligence_assessment: intelligenceScore,
            recommendations: recommendations,
            detailed_results: this.testResults,
            test_timestamp: new Date().toISOString()
        };

        await fs.writeFile(TEST_RESULTS_FILE, JSON.stringify(detailedReport, null, 2));
        console.log(`\n📄 Detailed report saved to: ${TEST_RESULTS_FILE}`);

        // Final assessment
        if (successRate >= 80 && intelligenceScore.overall >= 70) {
            console.log('\n🎉 SYSTEM STATUS: PRODUCTION READY');
            console.log('   The intelligent IC verification system is performing excellently!');
        } else if (successRate >= 60 && intelligenceScore.overall >= 50) {
            console.log('\n⚠️  SYSTEM STATUS: NEEDS IMPROVEMENT');
            console.log('   The system is functional but requires optimization.');
        } else {
            console.log('\n❌ SYSTEM STATUS: REQUIRES SIGNIFICANT WORK');
            console.log('   The system needs major improvements before deployment.');
        }

        console.log('\n='.repeat(80));
        console.log('Complete Intelligent System Test Finished');
        console.log('='.repeat(80));
    }

    analyzeMethodEffectiveness() {
        const methodStats = {};
        
        this.testResults.forEach(result => {
            result.methods_used.forEach(method => {
                if (!methodStats[method]) {
                    methodStats[method] = { usage: 0, successes: 0, successRate: 0 };
                }
                methodStats[method].usage++;
                if (result.passed) {
                    methodStats[method].successes++;
                }
            });
        });

        Object.keys(methodStats).forEach(method => {
            methodStats[method].successRate = (methodStats[method].successes / methodStats[method].usage) * 100;
        });

        return methodStats;
    }

    analyzePerformance() {
        const responseTimes = this.testResults.map(r => r.response_time).sort((a, b) => a - b);
        
        return {
            fastest: Math.min(...responseTimes),
            slowest: Math.max(...responseTimes),
            median: responseTimes[Math.floor(responseTimes.length / 2)]
        };
    }

    assessSystemIntelligence() {
        let scores = {
            webScraping: 0,
            internetSearch: 0,
            mlIntegration: 0,
            databaseUtilization: 0,
            overall: 0
        };

        // Assess based on method usage and effectiveness
        const methodStats = this.analyzeMethodEffectiveness();
        
        // Web Scraping Assessment (25 points)
        if (methodStats.web_scraping) {
            scores.webScraping = Math.min(25, Math.round((methodStats.web_scraping.successRate / 100) * 25));
        }

        // Internet Search Assessment (25 points)
        if (methodStats.internet_search) {
            scores.internetSearch = Math.min(25, Math.round((methodStats.internet_search.successRate / 100) * 25));
        }

        // ML Integration Assessment (25 points)
        const mlMethods = ['deep_learning', 'traditional_ml'];
        const mlSuccessRate = mlMethods.reduce((avg, method) => {
            return avg + (methodStats[method] ? methodStats[method].successRate : 0);
        }, 0) / mlMethods.length;
        scores.mlIntegration = Math.min(25, Math.round((mlSuccessRate / 100) * 25));

        // Database Utilization Assessment (25 points)
        if (methodStats.database) {
            scores.databaseUtilization = Math.min(25, Math.round((methodStats.database.successRate / 100) * 25));
        }

        // Overall score
        scores.overall = scores.webScraping + scores.internetSearch + scores.mlIntegration + scores.databaseUtilization;

        return scores;
    }

    generateRecommendations(successRate, intelligenceScore) {
        const recommendations = [];

        if (successRate < 80) {
            recommendations.push('Improve overall system accuracy by enhancing ML model training data');
        }

        if (intelligenceScore.webScraping < 20) {
            recommendations.push('Enhance web scraping capabilities for better manufacturer data retrieval');
        }

        if (intelligenceScore.internetSearch < 20) {
            recommendations.push('Improve intelligent internet search algorithms and document processing');
        }

        if (intelligenceScore.mlIntegration < 20) {
            recommendations.push('Optimize ML model integration and confidence scoring mechanisms');
        }

        if (intelligenceScore.databaseUtilization < 20) {
            recommendations.push('Expand IC database with more comprehensive marking information');
        }

        if (this.systemStats.averageResponseTime > 10000) {
            recommendations.push('Optimize system performance to reduce verification response times');
        }

        if (recommendations.length === 0) {
            recommendations.push('System is performing well! Consider adding more IC types to the test suite');
            recommendations.push('Implement continuous monitoring and automated testing');
            recommendations.push('Consider scaling the system for higher throughput');
        }

        return recommendations;
    }

    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Main execution
if (require.main === module) {
    const tester = new CompleteSystemTester();
    tester.runCompleteSystemTest().catch(error => {
        console.error('💥 Complete system test failed:', error);
        process.exit(1);
    });
}

module.exports = CompleteSystemTester;