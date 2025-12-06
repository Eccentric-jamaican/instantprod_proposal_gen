#!/usr/bin/env python3
"""
Environment verification script.
Checks that all dependencies and configurations are properly set up.
"""

import sys
from pathlib import Path

def check_python_version():
    """Verify Python version is 3.8+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"[FAIL] Python version {version.major}.{version.minor} is too old. Need 3.8+")
        return False

def check_dependencies():
    """Verify all required packages are installed"""
    required_packages = [
        'dotenv',
        'google.auth',
        'google_auth_oauthlib',
        'google_auth_httplib2',
        'googleapiclient',
        'pandas',
        'openpyxl',
        'requests',
        'click',
        'dateutil'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"[OK] {package}")
        except ImportError:
            print(f"[FAIL] {package} - NOT FOUND")
            missing.append(package)
    
    return len(missing) == 0

def check_directory_structure():
    """Verify required directories exist"""
    project_root = Path(__file__).parent
    required_dirs = [
        project_root / 'directives',
        project_root / 'execution',
        project_root / '.tmp'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"[OK] {dir_path.name}/")
        else:
            print(f"[FAIL] {dir_path.name}/ - MISSING")
            all_exist = False
    
    return all_exist

def check_env_file():
    """Check if .env file exists"""
    project_root = Path(__file__).parent
    env_file = project_root / '.env'
    
    if env_file.exists():
        print(f"[OK] .env file exists")
        return True
    else:
        print(f"[WARN] .env file not found (copy from .env.example)")
        return False

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Environment Verification")
    print("=" * 60)
    
    print("\n1. Python Version:")
    python_ok = check_python_version()
    
    print("\n2. Dependencies:")
    deps_ok = check_dependencies()
    
    print("\n3. Directory Structure:")
    dirs_ok = check_directory_structure()
    
    print("\n4. Configuration:")
    env_ok = check_env_file()
    
    print("\n" + "=" * 60)
    if python_ok and deps_ok and dirs_ok:
        print("[OK] Environment is ready!")
        if not env_ok:
            print("[WARN] Remember to configure your .env file with API keys")
        print("=" * 60)
        return 0
    else:
        print("[FAIL] Environment setup incomplete")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
