"""
Installation helper for Tesseract OCR on Windows
This script helps users install and configure Tesseract OCR for the IC Verification system.
"""

import os
import platform
import subprocess
import urllib.request
import sys

def check_admin():
    """Check if running with admin privileges"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def check_chocolatey():
    """Check if Chocolatey is installed"""
    try:
        result = subprocess.run(['choco', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def install_with_chocolatey():
    """Install Tesseract using Chocolatey"""
    if not check_admin():
        print("⚠️  Administrator privileges required for Chocolatey installation")
        print("   Please run PowerShell as Administrator and try again")
        return False
    
    try:
        print("📦 Installing Tesseract OCR using Chocolatey...")
        result = subprocess.run(['choco', 'install', 'tesseract', '-y'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Tesseract installed successfully via Chocolatey!")
            return True
        else:
            print(f"❌ Chocolatey installation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing via Chocolatey: {e}")
        return False

def check_existing_installation():
    """Check for existing Tesseract installation"""
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            print(f"✅ Found existing Tesseract installation: {path}")
            return path
    
    # Check if it's in PATH
    try:
        result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Tesseract found in system PATH")
            return "tesseract"
    except:
        pass
    
    return None

def manual_install_instructions():
    """Provide manual installation instructions"""
    print("\n" + "="*60)
    print("📋 MANUAL INSTALLATION INSTRUCTIONS")
    print("="*60)
    print("1. Download Tesseract OCR installer from:")
    print("   https://github.com/UB-Mannheim/tesseract/wiki")
    print("\n2. Choose the appropriate installer:")
    print("   - For 64-bit Windows: tesseract-ocr-w64-setup-5.x.x.exe")
    print("   - For 32-bit Windows: tesseract-ocr-w32-setup-5.x.x.exe")
    print("\n3. Run the installer as Administrator")
    print("\n4. During installation:")
    print("   - Keep the default installation path")
    print("   - Make sure 'Add to PATH' option is checked")
    print("\n5. After installation:")
    print("   - Restart your command prompt/PowerShell")
    print("   - Restart the API server")
    print("\n6. Verify installation by running:")
    print("   tesseract --version")
    print("="*60)

def main():
    print("🔍 Tesseract OCR Installation Helper")
    print("="*50)
    
    if platform.system() != "Windows":
        print("❌ This script is designed for Windows only")
        return
    
    # Check for existing installation
    existing = check_existing_installation()
    if existing:
        print("🎉 Tesseract is already installed and available!")
        print("   If you're still having issues, try restarting the API server")
        return
    
    print("❌ Tesseract OCR not found on this system")
    print("\n📦 Available installation options:")
    
    # Check installation options
    has_choco = check_chocolatey()
    is_admin = check_admin()
    
    if has_choco:
        print("1. ✅ Chocolatey (package manager)")
        if not is_admin:
            print("   ⚠️  Requires Administrator privileges")
    else:
        print("1. ❌ Chocolatey not available")
    
    print("2. ✅ Manual installation (recommended)")
    
    print("\n" + "="*50)
    
    # Get user choice
    if has_choco:
        choice = input("Choose installation method (1=Chocolatey, 2=Manual, q=quit): ").strip().lower()
    else:
        choice = input("Choose installation method (2=Manual, q=quit): ").strip().lower()
    
    if choice == 'q':
        print("Installation cancelled")
        return
    elif choice == '1' and has_choco:
        if install_with_chocolatey():
            print("🎉 Installation complete!")
            print("   Please restart the API server to use image verification")
        else:
            print("📋 Chocolatey installation failed, showing manual instructions...")
            manual_install_instructions()
    elif choice == '2':
        manual_install_instructions()
    else:
        print("❌ Invalid choice")
        manual_install_instructions()

if __name__ == "__main__":
    main()