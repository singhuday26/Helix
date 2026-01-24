"""
Helix Hackathon Submission Validator

Runs all critical checks before submitting to judges:
1. Syntax validation
2. Server startup test
3. API endpoint tests
4. Documentation completeness
5. Benchmark script verification
"""

import subprocess
import sys
import os
import time
import requests

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def check(name, passed, details=""):
    status = f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"
    print(f"{status} {name}")
    if details and not passed:
        print(f"  {YELLOW}{details}{RESET}")
    return passed

def main():
    print(f"\n{BOLD}{'='*60}")
    print("Helix Hackathon Submission Validator")
    print(f"{'='*60}{RESET}\n")
    
    passed = 0
    total = 0
    
    # Test 1: Syntax validation
    print(f"{BOLD}1. Syntax Validation{RESET}")
    total += 1
    try:
        result = subprocess.run(
            ["ven\\Scripts\\python.exe", "check_syntax.py"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if "✓ Syntax is valid!" in result.stdout:
            passed += check("Python syntax valid", True)
        else:
            check("Python syntax valid", False, result.stdout + result.stderr)
    except Exception as e:
        check("Python syntax valid", False, str(e))
    
    # Test 2: Critical imports
    print(f"\n{BOLD}2. Critical Imports{RESET}")
    modules = [
        "src.model_loader",
        "src.inference",
        "src.speculative",
        "src.kv_cache",
        "src.batch_optimizer",
        "src.api"
    ]
    for module in modules:
        total += 1
        try:
            result = subprocess.run(
                ["ven\\Scripts\\python.exe", "-c", f"import {module}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                passed += check(f"Import {module}", True)
            else:
                check(f"Import {module}", False, result.stderr)
        except Exception as e:
            check(f"Import {module}", False, str(e))
    
    # Test 3: Server startup (brief test)
    print(f"\n{BOLD}3. Server Startup Test{RESET}")
    total += 1
    server_proc = None
    try:
        # Start server
        server_proc = subprocess.Popen(
            ["ven\\Scripts\\python.exe", "run.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for startup (increased for model loading)
        time.sleep(15)
        
        # Test ping endpoint (lightweight health check)
        try:
            response = requests.get("http://localhost:8000/ping", timeout=5)
            if response.status_code == 200:
                passed += check("Server starts and responds", True)
            else:
                check("Server starts and responds", False, f"HTTP {response.status_code}")
        except requests.RequestException as e:
            check("Server starts and responds", False, str(e))
    except Exception as e:
        check("Server starts and responds", False, str(e))
    finally:
        if server_proc:
            server_proc.terminate()
            server_proc.wait(timeout=5)
    
    # Test 4: Documentation completeness
    print(f"\n{BOLD}4. Documentation Files{RESET}")
    docs = [
        "README.md",
        "ARCHITECTURE.md",
        "HACKATHON_SUBMISSION.md",
        "CLI_DEMO.md",
        "IMPLEMENTATION_PROGRESS.md"
    ]
    for doc in docs:
        total += 1
        if os.path.exists(doc):
            # Check file is not empty
            with open(doc, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) > 100:  # At least 100 chars
                    passed += check(f"Documentation: {doc}", True)
                else:
                    check(f"Documentation: {doc}", False, "File too short")
        else:
            check(f"Documentation: {doc}", False, "File not found")
    
    # Test 5: Benchmark scripts exist
    print(f"\n{BOLD}5. Benchmark Scripts{RESET}")
    scripts = [
        "benchmark_speculative.py",
        "test_streaming.py",
        "validate_codebase.py"
    ]
    for script in scripts:
        total += 1
        if os.path.exists(script):
            passed += check(f"Script: {script}", True)
        else:
            check(f"Script: {script}", False, "File not found")
    
    # Test 6: Critical code files
    print(f"\n{BOLD}6. Core Code Files{RESET}")
    code_files = [
        "src/inference.py",
        "src/speculative.py",
        "src/kv_cache.py",
        "src/batch_optimizer.py",
        "src/model_loader.py",
        "src/api.py",
        "run.py",
        "requirements.txt"
    ]
    for file in code_files:
        total += 1
        if os.path.exists(file):
            passed += check(f"Code: {file}", True)
        else:
            check(f"Code: {file}", False, "File not found")
    
    # Summary
    print(f"\n{BOLD}{'='*60}")
    print("Summary")
    print(f"{'='*60}{RESET}")
    print(f"Total Tests: {total}")
    print(f"{GREEN}Passed: {passed}{RESET}")
    print(f"{RED}Failed: {total - passed}{RESET}")
    
    percentage = (passed / total * 100) if total > 0 else 0
    print(f"\nScore: {percentage:.1f}%")
    
    if percentage >= 90:
        print(f"\n{GREEN}{BOLD}✓ SUBMISSION READY!{RESET}")
        print("\nNext steps:")
        print("  1. Record demo video (see CLI_DEMO.md)")
        print("  2. Push to GitHub: git push origin copilot")
        print("  3. Submit via hackathon portal")
    elif percentage >= 70:
        print(f"\n{YELLOW}{BOLD}⚠ MOSTLY READY - FIX FAILURES{RESET}")
        print("\nFix the failed tests above before submitting.")
    else:
        print(f"\n{RED}{BOLD}✗ NOT READY - CRITICAL ISSUES{RESET}")
        print("\nMultiple critical failures. Debug before submitting.")
    
    print(f"\n{BOLD}{'='*60}{RESET}\n")
    
    return percentage >= 90

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
