#!/usr/bin/env python3
"""
Quick API Endpoint Testing Script
Tests all available endpoints to ensure they're working correctly
"""

import requests
import json
import time
import sys

def test_endpoint(method, url, description, data=None, files=None):
    """Test a single API endpoint"""
    try:
        print(f"🔍 Testing {description}...")
        
        if method.upper() == 'GET':
            response = requests.get(url, timeout=10)
        elif method.upper() == 'POST':
            if files:
                response = requests.post(url, data=data, files=files, timeout=30)
            else:
                response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ {description}: SUCCESS")
            
            # Show relevant response data
            try:
                result = response.json()
                if 'status' in result:
                    print(f"   Status: {result.get('status')}")
                if 'total_count' in result:
                    print(f"   Records: {result.get('total_count')}")
                if 'database' in result and 'total_count' in result['database']:
                    print(f"   Database: {result['database']['total_count']} records")
                if 'services' in result:
                    services = result['services']
                    for service, status in services.items():
                        print(f"   {service}: {status.get('status', 'unknown')}")
            except:
                print(f"   Response length: {len(response.text)} chars")
        else:
            print(f"❌ {description}: FAILED ({response.status_code})")
            print(f"   Error: {response.text[:100]}...")
            
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print(f"❌ {description}: CONNECTION FAILED - Server not running")
        return False
    except requests.exceptions.Timeout:
        print(f"⏰ {description}: TIMEOUT - Server too slow")
        return False
    except Exception as e:
        print(f"❌ {description}: ERROR - {str(e)}")
        return False

def main():
    """Test all API endpoints"""
    print("🚀 IC Verification API - Endpoint Testing")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # Check if server is running
    print(f"🌐 Testing server at {base_url}...")
    
    tests = [
        # Core endpoints
        ("GET", f"{base_url}/", "API Home Page"),
        ("GET", f"{base_url}/health", "Health Check"),
        
        # Enhanced endpoints (v2)
        ("GET", f"{base_url}/api/v2/database", "Enhanced Database"),
        ("GET", f"{base_url}/api/v2/database/search?q=STM32", "Database Search"),
        
        # Model info
        ("GET", f"{base_url}/model_info", "Model Information"),
    ]
    
    # Run tests
    passed = 0
    total = len(tests)
    
    for method, url, description in tests:
        if test_endpoint(method, url, description):
            passed += 1
        time.sleep(0.5)  # Small delay between tests
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} endpoints working")
    
    if passed == total:
        print("🎉 All endpoints are working perfectly!")
        print("✅ Your API server is ready for use")
    elif passed >= total * 0.8:
        print("⚠️ Most endpoints working - system should be functional")
    else:
        print("❌ Many endpoints failed - check server configuration")
    
    print(f"\n💡 API Documentation available at: {base_url}")
    print("🔗 Key endpoints:")
    print(f"   • Health: {base_url}/health")
    print(f"   • Database: {base_url}/api/v2/database")
    print(f"   • Search: {base_url}/api/v2/database/search?q=STM32")
    
    return passed >= total * 0.8

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n⚠️  If tests failed, make sure to:")
        print("1. Start the API server: cd deep-learning-model && python enhanced_api_server.py")
        print("2. Check the server is running on port 5000")
        print("3. Verify all dependencies are installed")
    
    sys.exit(0 if success else 1)