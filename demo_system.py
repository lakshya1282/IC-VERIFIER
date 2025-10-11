#!/usr/bin/env python3
"""
IC Verification System Demo Script
Demonstrates the system's capabilities with sample ICs
"""

import requests
import json
import time
import sys
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:3000"
ENHANCED_API_URL = "http://localhost:5000"

# Sample ICs for demonstration
DEMO_ICS = [
    {
        "name": "STM32F103C8T6",
        "description": "ARM Cortex-M3 32-bit RISC core microcontroller",
        "expected_status": "AUTHENTIC",
        "manufacturer": "STMicroelectronics"
    },
    {
        "name": "ATmega328P",
        "description": "8-bit AVR microcontroller",
        "expected_status": "AUTHENTIC", 
        "manufacturer": "Microchip"
    },
    {
        "name": "ESP32-WROOM-32",
        "description": "Wi-Fi + Bluetooth module",
        "expected_status": "AUTHENTIC",
        "manufacturer": "Espressif Systems"
    },
    {
        "name": "LM555CN",
        "description": "Precision timer IC",
        "expected_status": "AUTHENTIC",
        "manufacturer": "Texas Instruments"
    },
    {
        "name": "FAKE12345",
        "description": "Simulated counterfeit IC",
        "expected_status": "FRAUD/UNKNOWN",
        "manufacturer": "Unknown"
    }
]

def print_banner():
    """Print system banner"""
    print("="*80)
    print("           IC VERIFICATION SYSTEM - LIVE DEMONSTRATION")
    print("                    SIH 2025-26 Prototype")
    print("="*80)
    print()

def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def verify_ic_demo(ic_data, api_url):
    """Demonstrate IC verification"""
    print(f"\n🔍 Verifying IC: {ic_data['name']}")
    print(f"   Description: {ic_data['description']}")
    print(f"   Expected: {ic_data['expected_status']}")
    print(f"   Manufacturer: {ic_data['manufacturer']}")
    print("   " + "-" * 50)
    
    try:
        # Try text verification
        response = requests.post(
            f"{api_url}/verify-text", 
            json={"marking_text": ic_data['name']},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status', 'Unknown')
            confidence = result.get('confidence', 0) * 100
            
            # Determine result indicator
            if 'AUTHENTIC' in status.upper():
                indicator = "✅"
            elif 'FRAUD' in status.upper() or 'UNKNOWN' in status.upper():
                indicator = "❌"
            else:
                indicator = "⚠️"
            
            print(f"   {indicator} Result: {status}")
            print(f"   📊 Confidence: {confidence:.1f}%")
            
            if result.get('matchedIC'):
                matched = result['matchedIC']
                print(f"   🏭 Matched Manufacturer: {matched.get('oemName', 'N/A')}")
                print(f"   🔧 IC Model: {matched.get('icModel', 'N/A')}")
            
            # Check if result matches expectation
            expected_authentic = 'AUTHENTIC' in ic_data['expected_status'].upper()
            actual_authentic = 'AUTHENTIC' in status.upper()
            
            if expected_authentic == actual_authentic:
                print("   ✅ Verification matches expectation")
            else:
                print("   ⚠️ Verification differs from expectation")
                
        else:
            print(f"   ❌ API Error: HTTP {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection Error: {str(e)}")
    except Exception as e:
        print(f"   ❌ Unexpected Error: {str(e)}")
    
    time.sleep(1)  # Brief pause for better visualization

def demonstrate_api_endpoints():
    """Demonstrate various API endpoints"""
    print_section("API ENDPOINTS DEMONSTRATION")
    
    endpoints_to_test = [
        ("/health", "System Health Check"),
        ("/stats", "Verification Statistics"), 
        ("/ic-database", "IC Database Access"),
        ("/ic-stats", "IC Statistics")
    ]
    
    for endpoint, description in endpoints_to_test:
        print(f"\n📡 Testing: {description}")
        print(f"   Endpoint: {BACKEND_URL}{endpoint}")
        
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                print("   ✅ Status: Online")
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        key_count = len(data.keys())
                        print(f"   📋 Data fields: {key_count}")
                        
                        # Show sample data for some endpoints
                        if endpoint == "/stats" and 'total_verifications' in data:
                            print(f"   📊 Total Verifications: {data['total_verifications']}")
                        elif endpoint == "/ic-stats" and 'total_ic_models' in data:
                            print(f"   💾 IC Models in Database: {data['total_ic_models']}")
                            
                except:
                    print("   📋 Non-JSON response received")
            else:
                print(f"   ❌ Status: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection Failed: {str(e)}")

def demonstrate_enhanced_features():
    """Demonstrate enhanced API features"""
    print_section("ENHANCED FEATURES DEMONSTRATION")
    
    enhanced_endpoints = [
        ("/api/v2/database", "Enhanced Database"),
        ("/api/v2/database/search?q=STM32", "Database Search"),
        ("/health", "Enhanced API Health")
    ]
    
    for endpoint, description in enhanced_endpoints:
        print(f"\n🚀 Testing: {description}")
        print(f"   Endpoint: {ENHANCED_API_URL}{endpoint}")
        
        try:
            response = requests.get(f"{ENHANCED_API_URL}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                print("   ✅ Status: Available")
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"   📋 Response keys: {list(data.keys())[:3]}")
                        
                        # Show specific enhanced features
                        if 'database' in data and 'total_count' in data['database']:
                            print(f"   💾 Database Records: {data['database']['total_count']}")
                        elif 'results' in data:
                            print(f"   🔍 Search Results: {len(data['results'])} found")
                            
                except:
                    print("   📋 Response received (non-JSON)")
            else:
                print(f"   ❌ Status: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection Failed: {str(e)}")

def show_system_info():
    """Display system information"""
    print_section("SYSTEM INFORMATION")
    
    print("🖥️  System Architecture:")
    print("   ├── Frontend (React): http://localhost:3001")
    print("   ├── Backend API: http://localhost:3000") 
    print("   ├── Enhanced API: http://localhost:5000")
    print("   └── Traditional ML: http://localhost:5001")
    print()
    
    print("⚡ Key Features:")
    print("   ├── OCR-based text extraction from IC images")
    print("   ├── Machine learning verification (100% accuracy on test dataset)")
    print("   ├── Traditional ML fallback system")  
    print("   ├── Comprehensive IC database with 30+ models")
    print("   ├── Real-time camera scanning")
    print("   ├── Image upload verification")
    print("   ├── Manual text entry verification")
    print("   └── Dashboard with statistics and analytics")
    print()
    
    print("📊 Database Coverage:")
    print("   ├── STMicroelectronics ICs")
    print("   ├── Microchip Technology ICs") 
    print("   ├── Texas Instruments ICs")
    print("   ├── Espressif Systems ICs")
    print("   ├── Analog Devices ICs")
    print("   └── And more...")

def run_interactive_demo():
    """Run interactive demonstration"""
    print_section("INTERACTIVE VERIFICATION DEMO")
    
    print("You can now test the system with custom IC markings!")
    print("Enter 'quit' to exit the demo")
    print()
    
    while True:
        user_input = input("🔍 Enter IC marking to verify (or 'quit'): ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
            
        if not user_input:
            print("   ⚠️ Please enter a valid IC marking")
            continue
        
        print(f"\n   Verifying: {user_input}")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/verify-text",
                json={"marking_text": user_input},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'Unknown')
                confidence = result.get('confidence', 0) * 100
                
                indicator = "✅" if 'AUTHENTIC' in status.upper() else "❌"
                print(f"   {indicator} Status: {status}")
                print(f"   📊 Confidence: {confidence:.1f}%")
                
                if result.get('matchedIC'):
                    matched = result['matchedIC']
                    print(f"   🏭 Manufacturer: {matched.get('oemName', 'N/A')}")
                    
            else:
                print(f"   ❌ Verification failed (HTTP {response.status_code})")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        print()

def main():
    """Main demo function"""
    print_banner()
    
    print("🎯 Welcome to the IC Verification System Demo!")
    print("This demonstration showcases our AI-powered counterfeit IC detection system.")
    print()
    print("💡 The system uses:")
    print("   • Deep Learning models trained on real IC datasets")  
    print("   • OCR technology for text extraction")
    print("   • Comprehensive IC database matching")
    print("   • Multi-tier verification approach")
    print()
    
    # Check system availability
    print("🔄 Checking system availability...")
    
    services = [
        (BACKEND_URL, "Backend API"),
        (ENHANCED_API_URL, "Enhanced API")
    ]
    
    available_services = []
    for url, name in services:
        try:
            response = requests.get(f"{url}/health", timeout=3)
            if response.status_code == 200:
                print(f"   ✅ {name}: Online")
                available_services.append((url, name))
            else:
                print(f"   ❌ {name}: Offline (HTTP {response.status_code})")
        except:
            print(f"   ❌ {name}: Offline (Connection failed)")
    
    if not available_services:
        print("\n❌ No services are currently running!")
        print("Please start the system using: start_system_simple.ps1")
        return
    
    # Show system info
    show_system_info()
    
    # API endpoints demo
    demonstrate_api_endpoints()
    
    # Enhanced features demo  
    demonstrate_enhanced_features()
    
    # IC verification demos
    print_section("IC VERIFICATION DEMONSTRATIONS")
    
    print("🧪 Testing with sample ICs...")
    print("This demonstrates the system's ability to distinguish authentic from counterfeit ICs.")
    
    # Use the first available service
    demo_api_url = available_services[0][0]
    
    for ic in DEMO_ICS:
        verify_ic_demo(ic, demo_api_url)
    
    # Interactive demo
    print("\n" + "="*60)
    response = input("Would you like to try the interactive demo? (y/n): ").strip().lower()
    
    if response in ['y', 'yes']:
        run_interactive_demo()
    
    # Closing
    print_section("DEMO COMPLETE")
    
    print("🎉 Thank you for exploring the IC Verification System!")
    print()
    print("📋 For more information:")
    print("   • View the usage guide: usage_guide.md")
    print("   • Run comprehensive tests: python test_system_comprehensive.py")
    print("   • Access the web interface: http://localhost:3001")
    print()
    print("🏆 This system represents a comprehensive solution for IC authenticity verification,")
    print("   combining cutting-edge AI with practical engineering to address counterfeit ICs.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
        print("Thank you for trying the IC Verification System!")
    except Exception as e:
        print(f"\n❌ Demo error: {str(e)}")
        print("Please check that the system is properly set up and running.")