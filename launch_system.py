#!/usr/bin/env python
"""
IC Verification System - Simple Launcher
Starts all components of the IC Verification System
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path
import requests
import threading

def print_banner():
    """Print welcome banner"""
    print("\n" + "="*70)
    print("   🔬 IC VERIFICATION SYSTEM LAUNCHER 🔬")
    print("          SIH 2025-26 | Version 2.0")
    print("="*70 + "\n")

def check_port(port):
    """Check if a port is available"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result != 0

def start_deep_learning_api():
    """Start the Deep Learning API server"""
    print("🚀 Starting Deep Learning API Server...")
    
    # Check if already running
    if not check_port(5000):
        try:
            response = requests.get("http://localhost:5000/health", timeout=2)
            if response.status_code == 200:
                print("✅ Deep Learning API already running on port 5000")
                return None
        except:
            pass
    
    # Start the server
    api_path = Path(__file__).parent / "deep-learning-model"
    os.chdir(api_path)
    
    process = subprocess.Popen(
        [sys.executable, "api_server_real.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )
    
    # Wait for server to start
    print("⏳ Waiting for API to initialize...")
    for i in range(30):
        time.sleep(1)
        try:
            response = requests.get("http://localhost:5000/health", timeout=1)
            if response.status_code == 200:
                print("✅ Deep Learning API Server started successfully!")
                return process
        except:
            continue
    
    print("⚠️ API server may not have started correctly")
    return process

def start_ml_api():
    """Start the traditional ML API server"""
    print("\n🤖 Starting Traditional ML API Server...")
    
    # Check if already running
    if not check_port(5001):
        print("⚠️ Port 5001 already in use, skipping ML API")
        return None
    
    # Start the server
    ml_path = Path(__file__).parent / "ml-model"
    if not ml_path.exists():
        print("⚠️ ML model directory not found, skipping")
        return None
    
    os.chdir(ml_path)
    
    # Check if model exists
    if not (ml_path / "ic_model.pkl").exists():
        print("📦 Training ML model first...")
        subprocess.run([sys.executable, "train_model.py"], check=False)
    
    process = subprocess.Popen(
        [sys.executable, "api_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )
    
    print("✅ Traditional ML API Server started")
    return process

def start_backend():
    """Start Node.js backend"""
    print("\n🖥️ Starting Node.js Backend...")
    
    # Check if already running
    if not check_port(3000):
        print("⚠️ Port 3000 already in use, skipping backend")
        return None
    
    backend_path = Path(__file__).parent / "backend"
    if not backend_path.exists():
        print("⚠️ Backend directory not found, skipping")
        return None
    
    os.chdir(backend_path)
    
    # Check if node_modules exist
    if not (backend_path / "node_modules").exists():
        print("📦 Installing backend dependencies...")
        subprocess.run("npm install", shell=True, check=False)
    
    process = subprocess.Popen(
        "npm start",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )
    
    print("✅ Node.js Backend started")
    return process

def start_frontend():
    """Start React frontend"""
    print("\n🎨 Starting React Frontend...")
    
    # Check if already running
    if not check_port(3001):
        print("⚠️ Port 3001 already in use, skipping frontend")
        return None
    
    frontend_path = Path(__file__).parent / "frontend"
    if not frontend_path.exists():
        print("⚠️ Frontend directory not found, skipping")
        return None
    
    os.chdir(frontend_path)
    
    # Check if node_modules exist
    if not (frontend_path / "node_modules").exists():
        print("📦 Installing frontend dependencies...")
        subprocess.run("npm install", shell=True, check=False)
    
    process = subprocess.Popen(
        "npm start",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )
    
    print("✅ React Frontend started")
    return process

def test_system():
    """Test the running system"""
    print("\n" + "="*70)
    print("🧪 Testing System Components...")
    print("="*70)
    
    tests = []
    
    # Test Deep Learning API
    try:
        response = requests.get("http://localhost:5000/health", timeout=2)
        if response.status_code == 200:
            tests.append(("Deep Learning API", True))
            print("✅ Deep Learning API: RUNNING")
        else:
            tests.append(("Deep Learning API", False))
            print("❌ Deep Learning API: NOT RESPONDING")
    except:
        tests.append(("Deep Learning API", False))
        print("❌ Deep Learning API: NOT RUNNING")
    
    # Test ML API
    try:
        response = requests.get("http://localhost:5001/api/health", timeout=2)
        if response.status_code == 200:
            tests.append(("Traditional ML API", True))
            print("✅ Traditional ML API: RUNNING")
    except:
        pass  # Optional component
    
    # Test Backend
    try:
        response = requests.get("http://localhost:3000/api/health", timeout=2)
        if response.status_code == 200:
            tests.append(("Backend", True))
            print("✅ Backend: RUNNING")
    except:
        pass  # Optional component
    
    # Test Frontend
    try:
        response = requests.get("http://localhost:3001", timeout=2)
        if response.status_code == 200:
            tests.append(("Frontend", True))
            print("✅ Frontend: RUNNING")
    except:
        pass  # Optional component
    
    # Summary
    passed = sum(1 for _, result in tests if result)
    print(f"\n📊 Test Results: {passed}/{len(tests)} components running")
    
    return passed > 0

def print_access_info():
    """Print access information"""
    print("\n" + "="*70)
    print("🌐 SYSTEM ACCESS POINTS")
    print("="*70)
    
    print("\n📡 Deep Learning API:")
    print("   • URL: http://localhost:5000")
    print("   • Health: http://localhost:5000/health")
    print("   • Verify: POST http://localhost:5000/verify")
    print("   • Process: POST http://localhost:5000/process")
    
    if not check_port(5001):
        print("\n🤖 Traditional ML API:")
        print("   • URL: http://localhost:5001/api")
    
    if not check_port(3000):
        print("\n🖥️ Backend API:")
        print("   • URL: http://localhost:3000/api")
    
    if not check_port(3001):
        print("\n🎨 Frontend Dashboard:")
        print("   • URL: http://localhost:3001")
        print("   • Open in browser to access the web interface")
    
    print("\n📝 Test Commands:")
    print("   curl http://localhost:5000/health")
    print('   curl -X POST -F "image=@test.jpg" http://localhost:5000/verify')
    print("   python deep-learning-model/test_system.py")

def run_test_client():
    """Run a simple test of the API"""
    print("\n" + "="*70)
    print("🔍 Running API Test...")
    print("="*70)
    
    try:
        # Create a simple test image
        import numpy as np
        import cv2
        
        # Create synthetic IC image
        img = np.ones((400, 600, 3), dtype=np.uint8) * 240
        cv2.rectangle(img, (50, 50), (550, 350), (60, 60, 60), -1)
        cv2.putText(img, 'TEST IC', (250, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Save and test
        test_path = "test_ic.jpg"
        cv2.imwrite(test_path, img)
        
        with open(test_path, 'rb') as f:
            files = {'image': f}
            response = requests.post("http://localhost:5000/verify", files=files, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Test Successful!")
            print(f"   • Status: {result.get('status')}")
            if 'results' in result:
                print(f"   • Detections: {result['results'].get('total_detections', 0)}")
                print(f"   • Authenticity: {result['results'].get('overall_authenticity', 'UNKNOWN')}")
        else:
            print(f"⚠️ API returned status code: {response.status_code}")
        
        # Clean up
        if os.path.exists(test_path):
            os.remove(test_path)
            
    except Exception as e:
        print(f"⚠️ Test failed: {e}")

def main():
    """Main launcher function"""
    print_banner()
    
    processes = []
    
    try:
        # Start Deep Learning API (required)
        dl_process = start_deep_learning_api()
        if dl_process:
            processes.append(dl_process)
        
        # Start optional components based on arguments
        if len(sys.argv) > 1:
            if "all" in sys.argv or "full" in sys.argv:
                # Start all components
                ml_process = start_ml_api()
                if ml_process:
                    processes.append(ml_process)
                
                backend_process = start_backend()
                if backend_process:
                    processes.append(backend_process)
                
                frontend_process = start_frontend()
                if frontend_process:
                    processes.append(frontend_process)
                    
                    # Open browser
                    import webbrowser
                    time.sleep(3)
                    webbrowser.open("http://localhost:3001")
            
            elif "api" in sys.argv:
                # Start both API servers
                ml_process = start_ml_api()
                if ml_process:
                    processes.append(ml_process)
        
        # Give services time to start
        time.sleep(3)
        
        # Test the system
        if test_system():
            print_access_info()
            
            # Run a test
            run_test_client()
            
            print("\n" + "="*70)
            print("✨ SYSTEM READY! Press Ctrl+C to stop all services.")
            print("="*70)
            
            # Keep running
            while True:
                time.sleep(1)
        else:
            print("\n❌ System failed to start properly")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Shutting down services...")
    finally:
        # Stop all processes
        for process in processes:
            if process:
                try:
                    if sys.platform == "win32":
                        subprocess.call(['taskkill', '/F', '/T', '/PID', str(process.pid)], 
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                except:
                    pass
        
        print("👋 All services stopped. Goodbye!")

if __name__ == "__main__":
    print("\nUsage:")
    print("  python launch_system.py          # Start essential API only")
    print("  python launch_system.py all      # Start all components")
    print("  python launch_system.py api      # Start both API servers")
    print()
    
    main()