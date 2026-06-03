#!/usr/bin/env python3
"""
Setup Verification Script
Checks if all dependencies and services are properly configured
"""

import sys
import subprocess
import os
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_python_version():
    """Check Python version"""
    print("✓ Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"  ❌ Python {version.major}.{version.minor}.{version.micro} (Need 3.11+)")
        return False

def check_ollama():
    """Check if Ollama is installed and running"""
    print("✓ Checking Ollama...")
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("  ✅ Ollama is installed and running")
            if 'llama3' in result.stdout:
                print("  ✅ llama3 model is available")
                return True
            else:
                print("  ⚠️  llama3 model not found. Run: ollama pull llama3")
                return False
        else:
            print("  ❌ Ollama is not running")
            return False
    except FileNotFoundError:
        print("  ❌ Ollama is not installed")
        print("     Install from: https://ollama.ai/download")
        return False
    except subprocess.TimeoutExpired:
        print("  ❌ Ollama command timed out")
        return False

def check_backend_dependencies():
    """Check if backend dependencies are installed"""
    print("✓ Checking backend dependencies...")
    
    if not os.path.exists('backend/venv') and not os.path.exists('backend/env'):
        print("  ⚠️  Virtual environment not found")
        print("     Create with: python -m venv backend/venv")
        return False
    
    try:
        # Try importing key packages
        sys.path.insert(0, 'backend')
        import fastapi
        import uvicorn
        import chromadb
        import sentence_transformers
        import ollama
        
        print("  ✅ All backend dependencies installed")
        return True
    except ImportError as e:
        print(f"  ❌ Missing dependency: {e.name}")
        print("     Install with: pip install -r backend/requirements.txt")
        return False

def check_frontend_dependencies():
    """Check if frontend dependencies are installed"""
    print("✓ Checking frontend dependencies...")
    
    if not os.path.exists('frontend/node_modules'):
        print("  ⚠️  node_modules not found")
        print("     Install with: cd frontend && npm install")
        return False
    
    if not os.path.exists('frontend/package.json'):
        print("  ❌ package.json not found")
        return False
    
    print("  ✅ Frontend dependencies installed")
    return True

def check_file_structure():
    """Check if all required files exist"""
    print("✓ Checking file structure...")
    
    required_files = [
        'backend/main.py',
        'backend/requirements.txt',
        'backend/api/upload.py',
        'backend/api/chat.py',
        'backend/services/rag_pipeline.py',
        'frontend/app/page.tsx',
        'frontend/components/ChatInterface.tsx',
        'frontend/lib/api.ts',
        'README.md',
        'QUICKSTART.md'
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print(f"  ❌ Missing files:")
        for file in missing:
            print(f"     - {file}")
        return False
    else:
        print("  ✅ All required files present")
        return True

def check_ports():
    """Check if required ports are available"""
    print("✓ Checking ports...")
    
    import socket
    
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    ports = {
        8000: 'Backend (FastAPI)',
        3000: 'Frontend (Next.js)',
        11434: 'Ollama'
    }
    
    issues = []
    for port, service in ports.items():
        if is_port_in_use(port):
            print(f"  ⚠️  Port {port} ({service}) is already in use")
            issues.append(port)
        else:
            print(f"  ✅ Port {port} ({service}) is available")
    
    return len(issues) == 0

def main():
    print_header("PDF RAG Chat - Setup Verification")
    
    checks = [
        ("Python Version", check_python_version),
        ("Ollama", check_ollama),
        ("Backend Dependencies", check_backend_dependencies),
        ("Frontend Dependencies", check_frontend_dependencies),
        ("File Structure", check_file_structure),
        ("Port Availability", check_ports)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ Error checking {name}: {e}")
            results.append((name, False))
    
    print_header("Verification Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! You're ready to run the application.")
        print("\nNext steps:")
        print("  1. Terminal 1: cd backend && uvicorn main:app --reload")
        print("  2. Terminal 2: cd frontend && npm run dev")
        print("  3. Open: http://localhost:3000")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("   See QUICKSTART.md for detailed setup instructions.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
