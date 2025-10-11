import React from 'react';
import TestRunner from '../components/TestRunner';

const TestPage = () => {
  return (
    <div style={{ 
      minHeight: '100vh',
      backgroundColor: '#f8f9fa',
      padding: '20px'
    }}>
      <div style={{
        maxWidth: '1000px',
        margin: '0 auto'
      }}>
        <div style={{
          textAlign: 'center',
          marginBottom: '30px',
          padding: '20px',
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #dee2e6'
        }}>
          <h1 style={{ color: '#495057', marginBottom: '10px' }}>
            🧪 IC Verifier - System Testing
          </h1>
          <p style={{ color: '#6c757d', margin: 0 }}>
            Comprehensive testing suite for frontend functionality and API integration
          </p>
        </div>
        
        <TestRunner />
        
        <div style={{
          marginTop: '30px',
          padding: '20px',
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #dee2e6',
          fontSize: '14px',
          color: '#495057'
        }}>
          <h3 style={{ marginTop: 0, color: '#495057' }}>🔍 What This Tests:</h3>
          <ul style={{ paddingLeft: '20px' }}>
            <li><strong>Service Availability:</strong> Checks if backend and ML API services are running</li>
            <li><strong>Health Checks:</strong> Verifies all services are responding correctly</li>
            <li><strong>API Integration:</strong> Tests all API endpoints used by the frontend</li>
            <li><strong>Data Retrieval:</strong> Validates statistics, database, and verification data</li>
            <li><strong>Error Handling:</strong> Confirms fallbacks and error handling work correctly</li>
            <li><strong>Component Integration:</strong> Ensures React components can access all API functions</li>
          </ul>
          
          <h3 style={{ color: '#495057' }}>📋 Test Coverage:</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '10px' }}>
            <div>
              <strong>Core APIs:</strong>
              <ul style={{ fontSize: '12px', marginTop: '5px' }}>
                <li>Health Check API</li>
                <li>Statistics API</li>
                <li>IC Database API</li>
                <li>Verification History</li>
              </ul>
            </div>
            <div>
              <strong>Verification APIs:</strong>
              <ul style={{ fontSize: '12px', marginTop: '5px' }}>
                <li>Text Verification</li>
                <li>Image Verification</li>
                <li>Comprehensive Verification</li>
                <li>Database Search</li>
              </ul>
            </div>
            <div>
              <strong>System Health:</strong>
              <ul style={{ fontSize: '12px', marginTop: '5px' }}>
                <li>Backend Server Status</li>
                <li>ML API Status</li>
                <li>MongoDB Connection</li>
                <li>Error Handling</li>
              </ul>
            </div>
          </div>
          
          <div style={{ 
            marginTop: '15px', 
            padding: '10px',
            backgroundColor: '#f8f9fa',
            borderRadius: '4px',
            borderLeft: '4px solid #007bff'
          }}>
            <strong>💡 Pro Tip:</strong> Run this test after starting all services to ensure everything is working correctly. 
            The tests will automatically use fallback data if some services are unavailable.
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestPage;