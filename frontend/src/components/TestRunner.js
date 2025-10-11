import React, { useState, useEffect } from 'react';
import { runFrontendTests } from '../utils/testRunner';

const TestRunner = () => {
  const [testResults, setTestResults] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [autoRun, setAutoRun] = useState(false);

  useEffect(() => {
    if (autoRun) {
      runTests();
    }
  }, [autoRun]);

  const runTests = async () => {
    setIsRunning(true);
    setTestResults(null);
    
    try {
      const results = await runFrontendTests();
      setTestResults(results);
    } catch (error) {
      console.error('Test execution failed:', error);
      setTestResults({
        passed: 0,
        failed: 1,
        tests: [{
          name: 'Test Execution',
          status: 'FAILED',
          error: error.message
        }]
      });
    } finally {
      setIsRunning(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'PASSED': return '#28a745';
      case 'FAILED': return '#dc3545';
      case 'SKIPPED': return '#ffc107';
      default: return '#6c757d';
    }
  };

  const getSuccessRateColor = (rate) => {
    if (rate >= 80) return '#28a745';
    if (rate >= 60) return '#ffc107';
    return '#dc3545';
  };

  const successRate = testResults && testResults.tests.length > 0 
    ? Math.round((testResults.passed / testResults.tests.length) * 100)
    : 0;

  return (
    <div style={{ 
      padding: '20px', 
      maxWidth: '800px', 
      margin: '0 auto',
      fontFamily: 'monospace',
      backgroundColor: '#f8f9fa',
      borderRadius: '8px',
      border: '1px solid #dee2e6'
    }}>
      <h2 style={{ color: '#495057', marginBottom: '20px' }}>
        🧪 Frontend Functionality Test Runner
      </h2>
      
      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={runTests}
          disabled={isRunning}
          style={{
            backgroundColor: isRunning ? '#6c757d' : '#007bff',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '4px',
            cursor: isRunning ? 'not-allowed' : 'pointer',
            marginRight: '10px',
            fontSize: '14px'
          }}
        >
          {isRunning ? '🔄 Running Tests...' : '▶️ Run All Tests'}
        </button>
        
        <label style={{ display: 'inline-flex', alignItems: 'center' }}>
          <input
            type="checkbox"
            checked={autoRun}
            onChange={(e) => setAutoRun(e.target.checked)}
            style={{ marginRight: '5px' }}
          />
          Auto-run on component mount
        </label>
      </div>

      {isRunning && (
        <div style={{ 
          padding: '15px',
          backgroundColor: '#d1ecf1',
          border: '1px solid #bee5eb',
          borderRadius: '4px',
          marginBottom: '20px',
          color: '#0c5460'
        }}>
          <div>🔄 Running comprehensive frontend tests...</div>
          <div style={{ fontSize: '12px', marginTop: '5px' }}>
            Check browser console for detailed logs
          </div>
        </div>
      )}

      {testResults && (
        <div style={{ marginTop: '20px' }}>
          <div style={{
            padding: '15px',
            backgroundColor: 'white',
            border: '1px solid #dee2e6',
            borderRadius: '4px',
            marginBottom: '20px'
          }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#495057' }}>
              📊 Test Results Summary
            </h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '10px' }}>
              <div>
                <strong>Total:</strong> {testResults.tests.length}
              </div>
              <div style={{ color: '#28a745' }}>
                <strong>Passed:</strong> {testResults.passed}
              </div>
              <div style={{ color: testResults.failed > 0 ? '#dc3545' : '#6c757d' }}>
                <strong>Failed:</strong> {testResults.failed}
              </div>
              <div style={{ color: getSuccessRateColor(successRate) }}>
                <strong>Success Rate:</strong> {successRate}%
              </div>
            </div>
          </div>

          <div style={{
            padding: '15px',
            backgroundColor: 'white',
            border: '1px solid #dee2e6',
            borderRadius: '4px'
          }}>
            <h3 style={{ margin: '0 0 15px 0', color: '#495057' }}>
              🔍 Detailed Results
            </h3>
            
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {testResults.tests.map((test, index) => (
                <div
                  key={index}
                  style={{
                    padding: '10px',
                    marginBottom: '8px',
                    backgroundColor: test.status === 'PASSED' ? '#f8f9fa' : '#fff5f5',
                    border: `1px solid ${getStatusColor(test.status)}`,
                    borderLeft: `4px solid ${getStatusColor(test.status)}`,
                    borderRadius: '4px'
                  }}
                >
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: test.error ? '5px' : '0'
                  }}>
                    <span style={{ fontWeight: 'bold' }}>
                      {test.name}
                    </span>
                    <span style={{
                      color: getStatusColor(test.status),
                      fontWeight: 'bold',
                      fontSize: '12px'
                    }}>
                      {test.status}
                    </span>
                  </div>
                  
                  {test.error && (
                    <div style={{
                      fontSize: '12px',
                      color: '#dc3545',
                      backgroundColor: '#f8d7da',
                      padding: '5px 8px',
                      borderRadius: '3px',
                      marginTop: '5px'
                    }}>
                      Error: {test.error}
                    </div>
                  )}
                  
                  {test.duration && (
                    <div style={{ fontSize: '11px', color: '#6c757d', marginTop: '3px' }}>
                      Duration: {test.duration}ms
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div style={{
            marginTop: '20px',
            padding: '10px',
            backgroundColor: getSuccessRateColor(successRate),
            color: 'white',
            borderRadius: '4px',
            textAlign: 'center',
            fontWeight: 'bold'
          }}>
            {successRate >= 80 && '✅ Frontend functionality is working well!'}
            {successRate >= 60 && successRate < 80 && '⚠️ Frontend has some issues but is mostly functional'}
            {successRate < 60 && '❌ Frontend has significant issues that need attention'}
          </div>
        </div>
      )}
      
      <div style={{ 
        marginTop: '20px', 
        fontSize: '12px', 
        color: '#6c757d',
        borderTop: '1px solid #dee2e6',
        paddingTop: '10px'
      }}>
        <p><strong>Note:</strong> This test runner checks all major frontend API integrations.</p>
        <p>For detailed logs and debugging information, check the browser console (F12).</p>
        <p>Some tests may show warnings if certain services are unavailable, but fallbacks should work.</p>
      </div>
    </div>
  );
};

export default TestRunner;