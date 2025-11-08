#!/usr/bin/env python3
"""Test script to verify Deafine installation."""

import sys
import subprocess
import os

def test_import(module_name):
    """Test if a module can be imported."""
    try:
        __import__(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {module_name}: {e}")
        return False

def test_optional_import(module_name):
    """Test if an optional module can be imported."""
    try:
        __import__(module_name)
        print(f"✅ {module_name} (optional - installed)")
        return True
    except ImportError:
        print(f"ℹ️  {module_name} (optional - not installed)")
        return True  # Not an error

def test_command(command):
    """Test if a command works."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ Command: {command}")
            return True
        else:
            print(f"❌ Command failed: {command}")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Command error: {command}")
        print(f"   Error: {e}")
        return False

def main():
    """Run installation tests."""
    print("🧪 Testing Deafine Installation\n")
    
    # Check Python version
    print("Python Version:")
    print(f"  {sys.version}")
    py_version = sys.version_info
    if py_version.major >= 3 and py_version.minor >= 9:
        print("✅ Python version is 3.9+\n")
    else:
        print("❌ Python version must be 3.9 or higher\n")
        return False
    
    # Test imports
    print("Testing Required Modules:")
    required_modules = [
        "sounddevice",
        "numpy",
        "soundfile",
        "rich",
        "typer",
        "dotenv",
        "httpx",
        "deafine"
    ]
    
    all_passed = True
    for module in required_modules:
        if not test_import(module):
            all_passed = False
    
    print()
    
    # Test optional imports
    print("Testing Optional Modules:")
    test_optional_import("webrtcvad")
    
    print()
    
    # Test deafine command
    print("Testing Deafine CLI:")
    if not test_command("deafine --help"):
        all_passed = False
    
    print()
    
    # Test audio device
    print("Testing Audio Device:")
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        
        if input_devices:
            print(f"✅ Found {len(input_devices)} input device(s):")
            for i, dev in enumerate(input_devices[:3]):  # Show first 3
                print(f"   {i+1}. {dev['name']}")
        else:
            print("❌ No input devices found")
            all_passed = False
    except Exception as e:
        print(f"❌ Audio test failed: {e}")
        all_passed = False
    
    print()
    
    # Check for .env file
    print("Checking Configuration:")
    if os.path.exists(".env"):
        print("✅ .env file exists")
        
        # Check for API key
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("ELEVEN_API_KEY", "")
        
        if api_key and api_key != "your_elevenlabs_api_key_here":
            print("✅ ELEVEN_API_KEY is set")
        else:
            print("⚠️  ELEVEN_API_KEY is not set in .env")
            print("   You need this to use Deafine!")
            all_passed = False
        
        # Check VAD setting
        use_vad = os.getenv("DEAFINE_USE_VAD", "true").lower() == "true"
        if use_vad:
            print("ℹ️  VAD enabled in config")
        else:
            print("ℹ️  VAD disabled in config")
    else:
        print("⚠️  .env file not found")
        print("   Run: cp env.template .env (or copy on Windows)")
        all_passed = False
    
    print()
    
    # VAD recommendation
    print("Voice Activity Detection (VAD) Status:")
    try:
        import webrtcvad
        print("✅ webrtcvad is installed")
        print("   💰 Saves ~60% in bandwidth and API costs")
    except ImportError:
        print("ℹ️  webrtcvad is NOT installed (optional)")
        print("   The app works fine without it!")
        print("   To save costs, install: pip install webrtcvad")
        print("   (Windows users: requires C++ Build Tools)")
    
    print()
    
    # Summary
    if all_passed:
        print("=" * 50)
        print("🎉 All tests passed!")
        print("=" * 50)
        print("\nYou can now run:")
        print("  deafine run")
    else:
        print("=" * 50)
        print("⚠️  Some tests failed")
        print("=" * 50)
        print("\nPlease check the errors above and refer to INSTALL.md")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
