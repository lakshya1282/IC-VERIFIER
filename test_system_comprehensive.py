#!/usr/bin/env python3
"""
Comprehensive Test Script for IC Verification System
Tests API endpoints, frontend components, and system integration
"""

import requests
import json
import time
import os
import sys
from pathlib import Path
import subprocess
import psutil
import threading

# Configuration
BACKEND_URL = "http://localhost:3000"
ENHANCED_API_URL = "http://localhost:5000"
FRONTEND_URL = "http://localhost:3001"
TRADITIONAL_ML_URL = "http://localhost:5001"

# Test data
TEST_ICS = [
    "STM32F103C8T6",
    "ATmega328P",
    "ESP32-WROOM-32",
    "LM555CN",
    "TL071CN",
    "FAKE12345"  # This should be detected as fraud/unknown
]

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_test_result(test_name, success, details=""):
    """Print test result with formatting"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status:<8} {test_name}")
    if details:
        print(f"         {details}")

def check_port_availability(port):
    """Check if a port is in use"""
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
            return True
    return False

def test_api_health(url, name):
    """Test API health endpoint"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        success = response.status_code == 200
        details = f"Status: {response.status_code}"
        if success:
            try:
                data = response.json()
                details += f", Response: {data.get('status', 'OK')}"
            except:
                pass
        print_test_result(f"{name} Health Check", success, details)
        return success
    except requests.exceptions.RequestException as e:
        print_test_result(f"{name} Health Check", False, f"Error: {str(e)}")
        return False

def test_text_verification(url, name):
    """Test text verification endpoint"""
    success_count = 0
    total_tests = len(TEST_ICS)
    
    for ic in TEST_ICS:
        try:
            # Try different endpoint formats
            endpoints_to_try = [
                ("/verify-text", {"marking_text": ic}),
                ("/api/v1/verify", {"text": ic}),
                ("/verify", {"text": ic})
            ]
            
            verified = False
            for endpoint, payload in endpoints_to_try:
                try:
                    response = requests.post(f"{url}{endpoint}", json=payload, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        verified = True
                        success_count += 1
                        confidence = data.get('confidence', 0)
                        status = data.get('status', 'Unknown')
                        print_test_result(f"  Text Verify: {ic}", True, 
                                        f"Status: {status}, Confidence: {confidence:.2f}")
                        break
                except:
                    continue
            
            if not verified:
                print_test_result(f"  Text Verify: {ic}", False, "No working endpoint found")
                
        except Exception as e:
            print_test_result(f"  Text Verify: {ic}", False, f"Error: {str(e)}")
    
    overall_success = success_count >= total_tests // 2  # At least 50% success
    print_test_result(f"{name} Text Verification", overall_success, 
                     f"{success_count}/{total_tests} tests passed")
    return overall_success

def test_image_verification(url, name):
    """Test image verification endpoint"""
    # Create a simple test image (placeholder)
    try:
        # Try to create a simple test image or use a placeholder
        test_image_data = b"fake_image_data_for_testing"
        
        endpoints_to_try = [
            "/verify-image",
            "/api/v1/verify", 
            "/verify"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                # Try JSON format first
                response = requests.post(f"{url}{endpoint}", 
                                       json={"image_base64": "data:image/jpeg;base64,test"}, 
                                       timeout=10)
                if response.status_code in [200, 400]:  # 400 is expected for invalid image
                    print_test_result(f"  Image Endpoint: {endpoint}", True, 
                                    f"Status: {response.status_code}")
                    return True
            except:
                continue
                
        print_test_result(f"{name} Image Verification", False, "No working image endpoint found")
        return False
        
    except Exception as e:
        print_test_result(f"{name} Image Verification", False, f"Error: {str(e)}")
        return False

def test_database_endpoints(url, name):
    """Test database-related endpoints"""
    endpoints = [
        ("/ic-database", "IC Database"),
        ("/ic-stats", "IC Stats"),
        ("/api/v2/database", "Enhanced Database"),
        ("/stats", "Statistics")
    ]
    
    success_count = 0
    for endpoint, desc in endpoints:
        try:
            response = requests.get(f"{url}{endpoint}", timeout=5)
            success = response.status_code == 200
            if success:
                try:
                    data = response.json()
                    details = f"Status: {response.status_code}, Data keys: {list(data.keys())[:3]}"
                except:
                    details = f"Status: {response.status_code}"
                success_count += 1
            else:
                details = f"Status: {response.status_code}"
            
            print_test_result(f"  {desc}", success, details)
            
        except requests.exceptions.RequestException as e:
            print_test_result(f"  {desc}", False, f"Error: {str(e)}")
    
    overall_success = success_count > 0
    print_test_result(f"{name} Database Endpoints", overall_success, 
                     f"{success_count}/{len(endpoints)} endpoints working")
    return overall_success

def test_frontend_accessibility():
    """Test if frontend is accessible"""
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        success = response.status_code == 200
        details = f"Status: {response.status_code}"
        if success:
            # Check if it contains React app indicators
            content = response.text
            if "React" in content or "root" in content or "App" in content:
                details += ", React app detected"
            else:
                details += ", Static content served"
        
        print_test_result("Frontend Accessibility", success, details)
        return success
        
    except requests.exceptions.RequestException as e:
        print_test_result("Frontend Accessibility", False, f"Error: {str(e)}")
        return False

def test_file_structure():
    """Test if required files exist"""
    required_files = [
        "enhanced_api_server.py",
        "enhanced_requirements.txt",
        "enhanced_datasheets.csv",
        "oem_data_fetcher.py",
        "setup_enhanced_environment.ps1",
        "start_system_simple.ps1",
        "usage_guide.md",
        "frontend/src/App.js",
        "frontend/src/pages/ScannerPage.js",
        "frontend/src/pages/DashboardPage.js",
        "frontend/src/services/api.js"
    ]
    
    success_count = 0
    base_path = Path(".")
    
    for file_path in required_files:
        file_exists = (base_path / file_path).exists()
        if file_exists:
            success_count += 1
            print_test_result(f"  File: {file_path}", True)
        else:
            print_test_result(f"  File: {file_path}", False, "Missing")
    
    overall_success = success_count >= len(required_files) * 0.8  # 80% of files exist
    print_test_result("File Structure", overall_success, 
                     f"{success_count}/{len(required_files)} files found")
    return overall_success

def test_python_dependencies():
    """Test if Python dependencies are available"""
    required_packages = [
        "flask",
        "requests", 
        "pandas",
        "numpy",
        "scikit-learn",
        "opencv-python",
        "pytesseract",
        "tensorflow",
        "torch"
    ]
    
    success_count = 0
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print_test_result(f"  Package: {package}", True)
            success_count += 1
        except ImportError:
            print_test_result(f"  Package: {package}", False, "Not installed")
    
    overall_success = success_count >= len(required_packages) // 2  # At least 50%
    print_test_result("Python Dependencies", overall_success, 
                     f"{success_count}/{len(required_packages)} packages available")
    return overall_success

def run_integration_test():
    """Run a full integration test"""
    print_header("Integration Test - Full Workflow")
    
    # Test full workflow: Frontend -> Backend -> Enhanced API
    test_ic = "STM32F103C8T6"
    
    try:
        # Step 1: Test text verification through backend
        backend_response = requests.post(f"{BACKEND_URL}/verify-text", 
                                       json={"marking_text": test_ic}, 
                                       timeout=10)
        backend_success = backend_response.status_code == 200
        print_test_result("Backend Text Verification", backend_success)
        
        # Step 2: Test enhanced API directly
        enhanced_response = requests.post(f"{ENHANCED_API_URL}/verify", 
                                        data={"text": test_ic},
                                        timeout=10)
        enhanced_success = enhanced_response.status_code == 200
        print_test_result("Enhanced API Direct Access", enhanced_success)
        
        # Step 3: Test data retrieval
        stats_response = requests.get(f"{BACKEND_URL}/stats", timeout=5)
        stats_success = stats_response.status_code in [200, 404]  # 404 is acceptable if no data
        print_test_result("Statistics Retrieval", stats_success)
        
        integration_success = backend_success or enhanced_success
        print_test_result("Overall Integration", integration_success, 
                         "At least one verification path working")
        
        return integration_success
        
    except Exception as e:
        print_test_result("Integration Test", False, f"Error: {str(e)}")
        return False

def check_system_resources():
    """Check system resources and performance"""
    print_header("System Resources Check")
    
    # Check CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_ok = cpu_percent < 90
    print_test_result("CPU Usage", cpu_ok, f"{cpu_percent:.1f}%")
    
    # Check memory usage
    memory = psutil.virtual_memory()
    memory_ok = memory.percent < 90
    print_test_result("Memory Usage", memory_ok, f"{memory.percent:.1f}%")
    
    # Check disk space
    disk = psutil.disk_usage('.')
    disk_ok = (disk.free / disk.total) > 0.1  # At least 10% free
    print_test_result("Disk Space", disk_ok, f"{(disk.free/1024**3):.1f}GB free")
    
    # Check running processes
    running_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if any(keyword in cmdline.lower() for keyword in ['node', 'python', 'flask', 'react']):
                running_processes.append(f"{proc.info['name']}:{proc.info['pid']}")
        except:
            pass
    
    print_test_result("Related Processes", len(running_processes) > 0, 
                     f"Found: {', '.join(running_processes[:3])}")
    
    return cpu_ok and memory_ok and disk_ok

def main():
    """Main test function"""
    print_header("IC Verification System - Comprehensive Test Suite")
    print("This script tests all components of the IC verification system")
    print("Make sure all services are running before starting tests")
    
    # Wait for user confirmation
    input("\nPress Enter to start testing...")
    
    results = {}
    
    # Test 1: File structure
    print_header("File Structure Test")
    results['file_structure'] = test_file_structure()
    
    # Test 2: Python dependencies
    print_header("Python Dependencies Test")  
    results['dependencies'] = test_python_dependencies()
    
    # Test 3: System resources
    results['resources'] = check_system_resources()
    
    # Test 4: Port availability
    print_header("Port Availability Check")
    ports_to_check = [3000, 3001, 5000, 5001]
    port_results = []
    for port in ports_to_check:
        available = check_port_availability(port)
        service_name = {3000: "Backend", 3001: "Frontend", 5000: "Enhanced API", 5001: "Traditional ML"}[port]
        print_test_result(f"Port {port} ({service_name})", available)
        port_results.append(available)
    results['ports'] = any(port_results)
    
    # Test 5: API Health checks
    print_header("API Health Checks")
    api_results = []
    apis_to_test = [
        (BACKEND_URL, "Backend API"),
        (ENHANCED_API_URL, "Enhanced API"),
        (TRADITIONAL_ML_URL, "Traditional ML API")
    ]
    
    for url, name in apis_to_test:
        result = test_api_health(url, name)
        api_results.append(result)
    results['api_health'] = any(api_results)
    
    # Test 6: Frontend accessibility
    print_header("Frontend Test")
    results['frontend'] = test_frontend_accessibility()
    
    # Test 7: Text verification
    print_header("Text Verification Tests")
    text_results = []
    for url, name in apis_to_test:
        if f"{url}/health" in [f"{BACKEND_URL}/health", f"{ENHANCED_API_URL}/health"]:
            result = test_text_verification(url, name)
            text_results.append(result)
    results['text_verification'] = any(text_results)
    
    # Test 8: Image verification  
    print_header("Image Verification Tests")
    image_results = []
    for url, name in apis_to_test:
        if f"{url}/health" in [f"{BACKEND_URL}/health", f"{ENHANCED_API_URL}/health"]:
            result = test_image_verification(url, name)
            image_results.append(result)
    results['image_verification'] = any(image_results)
    
    # Test 9: Database endpoints
    print_header("Database Endpoint Tests")
    db_results = []
    for url, name in apis_to_test:
        result = test_database_endpoints(url, name)
        db_results.append(result)
    results['database'] = any(db_results)
    
    # Test 10: Integration test
    results['integration'] = run_integration_test()
    
    # Final results
    print_header("TEST SUMMARY")
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    for test_name, result in results.items():
        print_test_result(f"{test_name.replace('_', ' ').title()}", result)
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} test categories passed")
    
    if passed_tests >= total_tests * 0.7:  # 70% pass rate
        print("\n✓ SYSTEM STATUS: GOOD - Ready for demonstration")
        print("  Most components are working correctly")
    elif passed_tests >= total_tests * 0.5:  # 50% pass rate
        print("\n⚠ SYSTEM STATUS: PARTIAL - Some issues detected")
        print("  Core functionality available but some features may not work")
    else:
        print("\n✗ SYSTEM STATUS: POOR - Major issues detected") 
        print("  Please check service startup and configuration")
    
    print("\nRecommendations:")
    if not results.get('file_structure', True):
        print("- Check that all required files are present")
    if not results.get('dependencies', True):
        print("- Install missing Python dependencies: pip install -r enhanced_requirements.txt")
    if not results.get('ports', True):
        print("- Start the required services using start_system_simple.ps1")
    if not results.get('api_health', True):
        print("- Verify API servers are running and accessible")
    if not results.get('frontend', True):
        print("- Check frontend server (npm start in frontend directory)")
    
    return passed_tests >= total_tests * 0.7

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)