"""
IC Verification System - Complete System Launcher
Runs all components of the IC Verification System
"""

import os
import sys
import time
import subprocess
import threading
import json
import signal
import psutil
from pathlib import Path
from datetime import datetime
import requests
import webbrowser
from typing import Dict, List, Optional

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ICVerificationSystemLauncher:
    """Master launcher for the IC Verification System"""
    
    def __init__(self):
        self.base_path = Path(os.path.dirname(os.path.abspath(__file__)))
        self.processes = {}
        self.running_services = []
        self.log_file = self.base_path / 'system_launch.log'
        
        # Service configurations
        self.services = {
            'ml_api': {
                'name': 'ML API Server (Traditional)',
                'path': self.base_path / 'ml-model',
                'command': 'python api_server.py',
                'port': 5001,
                'required': False,
                'health_endpoint': 'http://localhost:5001/api/health'
            },
            'deep_learning_api': {
                'name': 'Deep Learning API Server',
                'path': self.base_path / 'deep-learning-model',
                'command': 'python api_server_real.py',
                'port': 5000,
                'required': True,
                'health_endpoint': 'http://localhost:5000/health'
            },
            'backend': {
                'name': 'Node.js Backend',
                'path': self.base_path / 'backend',
                'command': 'npm start',
                'port': 3000,
                'required': False,
                'health_endpoint': 'http://localhost:3000/api/health',
                'setup_command': 'npm install'
            },
            'frontend': {
                'name': 'React Frontend',
                'path': self.base_path / 'frontend',
                'command': 'npm start',
                'port': 3001,
                'required': False,
                'health_endpoint': None,
                'setup_command': 'npm install'
            }
        }
    
    def print_banner(self):
        """Print system banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║       🔬 IC VERIFICATION SYSTEM - COMPLETE LAUNCHER 🔬              ║
║                                                                      ║
║                    SIH 2025-26 | Version 2.0                        ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
        """
        print(f"{Colors.CYAN}{banner}{Colors.ENDC}")
        print(f"{Colors.GREEN}📅 Launch Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
        print("="*72)
    
    def log(self, message: str, level: str = "INFO"):
        """Log messages to file and console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}"
        
        # Console output with colors
        if level == "ERROR":
            print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")
        elif level == "WARNING":
            print(f"{Colors.WARNING}⚠️ {message}{Colors.ENDC}")
        elif level == "SUCCESS":
            print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")
        else:
            print(f"ℹ️ {message}")
        
        # File logging
        with open(self.log_file, 'a') as f:
            f.write(log_message + '\n')
    
    def check_python_packages(self) -> Dict[str, bool]:
        """Check if required Python packages are installed"""
        required_packages = {
            'torch': 'PyTorch',
            'flask': 'Flask',
            'numpy': 'NumPy',
            'cv2': 'OpenCV',
            'onnxruntime': 'ONNX Runtime',
            'requests': 'Requests'
        }
        
        installed = {}
        self.log("Checking Python packages...")
        
        for package, name in required_packages.items():
            try:
                __import__(package)
                installed[name] = True
                self.log(f"  ✓ {name} installed", "SUCCESS")
            except ImportError:
                installed[name] = False
                self.log(f"  ✗ {name} not installed", "WARNING")
        
        return installed
    
    def check_node_modules(self, service_path: Path) -> bool:
        """Check if node_modules exist for Node.js projects"""
        node_modules = service_path / 'node_modules'
        package_json = service_path / 'package.json'
        
        if package_json.exists():
            if not node_modules.exists():
                self.log(f"Node modules not found in {service_path.name}", "WARNING")
                return False
            return True
        return True
    
    def install_dependencies(self, service_name: str, service_config: dict) -> bool:
        """Install dependencies for a service"""
        if 'setup_command' in service_config:
            self.log(f"Installing dependencies for {service_name}...")
            try:
                process = subprocess.run(
                    service_config['setup_command'],
                    shell=True,
                    cwd=service_config['path'],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if process.returncode == 0:
                    self.log(f"Dependencies installed for {service_name}", "SUCCESS")
                    return True
                else:
                    self.log(f"Failed to install dependencies for {service_name}", "ERROR")
                    return False
            except Exception as e:
                self.log(f"Error installing dependencies: {e}", "ERROR")
                return False
        return True
    
    def check_port(self, port: int) -> bool:
        """Check if a port is available"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                return False
        return True
    
    def start_service(self, service_name: str, service_config: dict) -> bool:
        """Start a single service"""
        try:
            # Check if port is available
            if not self.check_port(service_config['port']):
                self.log(f"Port {service_config['port']} is already in use", "WARNING")
                # Try to check if it's our service
                if service_config.get('health_endpoint'):
                    try:
                        response = requests.get(service_config['health_endpoint'], timeout=2)
                        if response.status_code == 200:
                            self.log(f"{service_name} already running on port {service_config['port']}", "SUCCESS")
                            self.running_services.append(service_name)
                            return True
                    except:
                        pass
                return False
            
            # Change to service directory
            os.chdir(service_config['path'])
            
            # Start the service
            self.log(f"Starting {service_config['name']}...")
            
            if sys.platform == "win32":
                # Windows specific
                process = subprocess.Popen(
                    service_config['command'],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                # Unix/Linux
                process = subprocess.Popen(
                    service_config['command'],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid
                )
            
            self.processes[service_name] = process
            
            # Wait for service to start
            time.sleep(3)
            
            # Check if service is running
            if process.poll() is None:
                self.log(f"{service_config['name']} started (PID: {process.pid})", "SUCCESS")
                self.running_services.append(service_name)
                return True
            else:
                self.log(f"Failed to start {service_config['name']}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error starting {service_name}: {e}", "ERROR")
            return False
    
    def wait_for_service(self, service_name: str, service_config: dict, timeout: int = 30) -> bool:
        """Wait for a service to be ready"""
        if not service_config.get('health_endpoint'):
            return True
        
        self.log(f"Waiting for {service_name} to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(service_config['health_endpoint'], timeout=2)
                if response.status_code == 200:
                    self.log(f"{service_name} is ready!", "SUCCESS")
                    return True
            except:
                pass
            time.sleep(1)
        
        self.log(f"Timeout waiting for {service_name}", "WARNING")
        return False
    
    def test_system(self):
        """Test the running system"""
        self.log("\n" + "="*72)
        self.log("Running System Tests...")
        self.log("="*72)
        
        test_results = []
        
        # Test Deep Learning API
        if 'deep_learning_api' in self.running_services:
            try:
                # Test health endpoint
                response = requests.get('http://localhost:5000/health', timeout=5)
                if response.status_code == 200:
                    test_results.append(('Deep Learning API Health', True))
                    
                    # Test model info
                    response = requests.get('http://localhost:5000/model_info', timeout=5)
                    test_results.append(('Model Info Endpoint', response.status_code == 200))
                else:
                    test_results.append(('Deep Learning API Health', False))
            except Exception as e:
                test_results.append(('Deep Learning API', False))
                self.log(f"API test failed: {e}", "ERROR")
        
        # Test Backend API
        if 'backend' in self.running_services:
            try:
                response = requests.get('http://localhost:3000/api/health', timeout=5)
                test_results.append(('Backend API Health', response.status_code == 200))
            except:
                test_results.append(('Backend API Health', False))
        
        # Test Frontend
        if 'frontend' in self.running_services:
            try:
                response = requests.get('http://localhost:3001', timeout=5)
                test_results.append(('Frontend Accessible', response.status_code == 200))
            except:
                test_results.append(('Frontend Accessible', False))
        
        # Print test results
        self.log("\n📊 Test Results:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"  {test_name}: {status}")
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        self.log(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        return passed == total
    
    def print_access_info(self):
        """Print access information for running services"""
        self.log("\n" + "="*72)
        self.log("🌐 Access Points:", "SUCCESS")
        self.log("="*72)
        
        if 'deep_learning_api' in self.running_services:
            print(f"\n{Colors.CYAN}📡 Deep Learning API Server:{Colors.ENDC}")
            print(f"   URL: {Colors.GREEN}http://localhost:5000{Colors.ENDC}")
            print(f"   • Health Check: http://localhost:5000/health")
            print(f"   • Verify IC: POST http://localhost:5000/verify")
            print(f"   • Full Process: POST http://localhost:5000/process")
        
        if 'ml_api' in self.running_services:
            print(f"\n{Colors.CYAN}🤖 Traditional ML API:{Colors.ENDC}")
            print(f"   URL: {Colors.GREEN}http://localhost:5001{Colors.ENDC}")
        
        if 'backend' in self.running_services:
            print(f"\n{Colors.CYAN}🖥️ Backend API:{Colors.ENDC}")
            print(f"   URL: {Colors.GREEN}http://localhost:3000{Colors.ENDC}")
            print(f"   • API Health: http://localhost:3000/api/health")
            print(f"   • Verifications: http://localhost:3000/api/verifications")
        
        if 'frontend' in self.running_services:
            print(f"\n{Colors.CYAN}🎨 Frontend Dashboard:{Colors.ENDC}")
            print(f"   URL: {Colors.GREEN}http://localhost:3001{Colors.ENDC}")
            print(f"   • Dashboard: http://localhost:3001/")
            print(f"   • Scanner: http://localhost:3001/scanner")
        
        print(f"\n{Colors.YELLOW}📝 Test Commands:{Colors.ENDC}")
        print("   • Test with cURL:")
        print('     curl http://localhost:5000/health')
        print('     curl -X POST -F "image=@test.jpg" http://localhost:5000/verify')
        print("\n   • Test with Python:")
        print("     python test_system.py")
    
    def stop_all_services(self):
        """Stop all running services"""
        self.log("\n🛑 Stopping all services...")
        
        for service_name, process in self.processes.items():
            try:
                if sys.platform == "win32":
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(process.pid)], 
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                
                self.log(f"Stopped {service_name}", "SUCCESS")
            except:
                pass
        
        self.processes.clear()
        self.running_services.clear()
    
    def run(self, mode: str = "full"):
        """
        Run the IC Verification System
        
        Args:
            mode: 'full' - Run all components
                  'api' - Run only API servers
                  'essential' - Run only deep learning API
        """
        try:
            self.print_banner()
            
            # Check Python packages
            packages = self.check_python_packages()
            
            # Determine which services to start based on mode
            services_to_start = []
            
            if mode == "essential":
                services_to_start = ['deep_learning_api']
                self.log("Running in ESSENTIAL mode (Deep Learning API only)")
            elif mode == "api":
                services_to_start = ['deep_learning_api', 'ml_api']
                self.log("Running in API mode (API servers only)")
            else:  # full
                services_to_start = ['deep_learning_api', 'backend', 'frontend']
                self.log("Running in FULL mode (All components)")
            
            # Start services
            self.log("\n🚀 Starting Services...")
            self.log("="*72)
            
            for service_name in services_to_start:
                if service_name not in self.services:
                    continue
                
                service_config = self.services[service_name]
                
                # Check and install dependencies if needed
                if service_name in ['backend', 'frontend']:
                    if not self.check_node_modules(service_config['path']):
                        self.install_dependencies(service_name, service_config)
                
                # Start the service
                if self.start_service(service_name, service_config):
                    # Wait for service to be ready
                    self.wait_for_service(service_name, service_config)
                elif service_config.get('required', False):
                    self.log(f"Failed to start required service: {service_name}", "ERROR")
                    self.stop_all_services()
                    return False
            
            # Give services time to fully initialize
            time.sleep(2)
            
            # Run tests
            if self.running_services:
                self.test_system()
                self.print_access_info()
                
                # Open browser if frontend is running
                if 'frontend' in self.running_services:
                    self.log("\n🌐 Opening browser...")
                    webbrowser.open('http://localhost:3001')
                
                self.log("\n" + "="*72)
                self.log("✨ SYSTEM READY! Press Ctrl+C to stop all services.", "SUCCESS")
                self.log("="*72)
                
                # Keep running until interrupted
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    self.log("\n\n⚠️ Shutdown signal received...")
            else:
                self.log("No services were started successfully", "ERROR")
                return False
                
        except KeyboardInterrupt:
            self.log("\n\nShutdown requested by user", "WARNING")
        except Exception as e:
            self.log(f"Unexpected error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
        finally:
            self.stop_all_services()
            self.log("\n👋 System shutdown complete. Goodbye!", "SUCCESS")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='IC Verification System Launcher')
    parser.add_argument('--mode', choices=['full', 'api', 'essential'], 
                       default='essential',
                       help='Launch mode: full (all components), api (APIs only), essential (deep learning API only)')
    parser.add_argument('--no-browser', action='store_true',
                       help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    # Create and run launcher
    launcher = ICVerificationSystemLauncher()
    
    # Disable browser opening if requested
    if args.no_browser:
        webbrowser.open = lambda url: None
    
    launcher.run(mode=args.mode)

if __name__ == "__main__":
    main()