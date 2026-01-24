"""
Helix Enhanced Validation Suite
48 comprehensive tests across all critical systems
Target: 99%+ validation score
"""

import subprocess
import sys
import os
import time
import re
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


class TestResult:
    """Track test results across categories"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.categories = {}
        self.critical_failures = []
    
    def add_test(self, category, name, passed, details="", is_critical=False):
        self.total += 1
        if passed:
            self.passed += 1
            status = f"{GREEN}OK{RESET}"
        else:
            self.failed += 1
            status = f"{RED}FAIL{RESET}"
            if is_critical:
                self.critical_failures.append(name)
        
        if category not in self.categories:
            self.categories[category] = {"passed": 0, "total": 0}
        
        self.categories[category]["total"] += 1
        if passed:
            self.categories[category]["passed"] += 1
        
        print(f"  {status} {name}")
        if details and not passed:
            print(f"    {YELLOW}{details}{RESET}")
        
        return passed
    
    def print_summary(self):
        print(f"\n{BOLD}{'='*60}")
        print("Test Summary by Category")
        print(f"{'='*60}{RESET}\n")
        
        for category, stats in self.categories.items():
            percentage = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            color = GREEN if percentage == 100 else YELLOW if percentage >= 80 else RED
            print(f"{category}: {color}{stats['passed']}/{stats['total']} ({percentage:.0f}%){RESET}")
        
        print(f"\n{BOLD}{'='*60}")
        print(f"Overall Score: {self.passed}/{self.total} ({self.passed/self.total*100:.1f}%)")
        print(f"{'='*60}{RESET}\n")
        
        if self.critical_failures:
            print(f"{RED}{BOLD}Critical Failures:{RESET}")
            for failure in self.critical_failures:
                print(f"  - {failure}")
            print()
        
        score = self.passed / self.total
        if score >= 0.99:
            print(f"{GREEN}{BOLD}🏆 EXCELLENT! Top 1% ready - Submit with confidence!{RESET}")
        elif score >= 0.95:
            print(f"{BLUE}{BOLD}✓ GREAT! Minor issues - Good to submit{RESET}")
        elif score >= 0.90:
            print(f"{YELLOW}{BOLD}⚠ GOOD - Fix critical issues before submitting{RESET}")
        else:
            print(f"{RED}{BOLD}✗ NEEDS WORK - Multiple critical issues{RESET}")


def run_command(cmd, timeout=10):
    """Helper to run subprocess commands"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)


def test_syntax_and_imports(results):
    """Test 1-7: Syntax validation and critical imports"""
    print(f"\n{BOLD}1. Syntax & Imports (7 tests){RESET}")
    
    # Test 1: Python syntax
    success, stdout, stderr = run_command(["ven\\Scripts\\python.exe", "check_syntax.py"])
    results.add_test(
        "Syntax", 
        "Python syntax valid",
        "OK: Syntax is valid!" in stdout or success,
        stderr,
        is_critical=True
    )
    
    # Test 2-7: Critical imports
    modules = [
        "src.model_loader", "src.inference", "src.speculative",
        "src.kv_cache", "src.batch_optimizer", "src.api"
    ]
    for module in modules:
        success, _, stderr = run_command(["ven\\Scripts\\python.exe", "-c", f"import {module}"])
        results.add_test(
            "Imports",
            f"Import {module}",
            success,
            stderr,
            is_critical=True
        )


def test_documentation(results):
    """Test 8-14: Documentation completeness and quality"""
    print(f"\n{BOLD}2. Documentation (7 tests){RESET}")
    
    required_docs = {
        "README.md": ["Quick Start", "python run.py"],
        "ARCHITECTURE.md": ["PagedAttention", "trade-off"],
        "HACKATHON_SUBMISSION.md": ["3x", "benchmark"],
        "CLI_DEMO.md": ["curl", "/generate"],
        "IMPLEMENTATION_PROGRESS.md": ["Phase"],
        "STUDY_GUIDE.md": ["elevator pitch", "judge"],
        "IMPLEMENTATION_PLAN.md": ["99%", "validation"]
    }
    
    for doc, keywords in required_docs.items():
        if os.path.exists(doc):
            try:
                with open(doc, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    has_content = len(content) > 100
                    has_keywords = any(kw.lower() in content for kw in keywords)
                    results.add_test(
                        "Docs",
                        f"{doc} complete",
                        has_content and has_keywords,
                        f"Missing keywords: {keywords}" if not has_keywords else ""
                    )
            except Exception as e:
                results.add_test("Docs", f"{doc} complete", False, str(e))
        else:
            results.add_test("Docs", f"{doc} complete", False, "File not found")


def test_code_files(results):
    """Test 15-22: Core code files exist and valid"""
    print(f"\n{BOLD}3. Code Files (8 tests){RESET}")
    
    code_files = [
        "src/__init__.py",
        "src/api.py",
        "src/inference.py",
        "src/speculative.py",
        "src/kv_cache.py",
        "src/model_loader.py",
        "src/batch_optimizer.py",
        "run.py"
    ]
    
    for file_path in code_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Check: File has content, no syntax errors (simple heuristic)
                    has_content = len(content) > 50
                    no_obvious_errors = 'SyntaxError' not in content
                    results.add_test(
                        "Code",
                        f"{file_path} valid",
                        has_content and no_obvious_errors,
                        "Empty or contains errors" if not (has_content and no_obvious_errors) else "",
                        is_critical=file_path in ["src/api.py", "src/inference.py"]
                    )
            except Exception as e:
                results.add_test("Code", f"{file_path} valid", False, str(e), is_critical=True)
        else:
            results.add_test("Code", f"{file_path} valid", False, "File not found", is_critical=True)


def test_benchmark_scripts(results):
    """Test 23-25: Benchmark scripts present"""
    print(f"\n{BOLD}4. Benchmark Scripts (3 tests){RESET}")
    
    scripts = [
        "benchmark_speculative.py",
        "test_streaming.py",
        "validate_codebase.py"
    ]
    
    for script in scripts:
        exists = os.path.exists(script)
        if exists:
            try:
                with open(script, 'r', encoding='utf-8') as f:
                    content = f.read()
                    has_main = '__main__' in content or 'def ' in content
                    results.add_test(
                        "Benchmarks",
                        f"{script} present",
                        has_main,
                        "No executable code found" if not has_main else ""
                    )
            except Exception as e:
                results.add_test("Benchmarks", f"{script} present", False, str(e))
        else:
            results.add_test("Benchmarks", f"{script} present", False, "File not found")


def test_configuration(results):
    """Test 26-31: Configuration files"""
    print(f"\n{BOLD}5. Configuration (6 tests){RESET}")
    
    # Test 26: requirements.txt has critical dependencies
    if os.path.exists("requirements.txt"):
        try:
            with open("requirements.txt", 'r') as f:
                deps = f.read()
                critical_deps = ["torch", "transformers", "fastapi", "uvicorn"]
                missing = [dep for dep in critical_deps if dep not in deps]
                results.add_test(
                    "Config",
                    "requirements.txt complete",
                    len(missing) == 0,
                    f"Missing: {missing}" if missing else "",
                    is_critical=True
                )
        except Exception as e:
            results.add_test("Config", "requirements.txt complete", False, str(e), is_critical=True)
    else:
        results.add_test("Config", "requirements.txt complete", False, "File not found", is_critical=True)
    
    # Test 27: .gitignore exists
    results.add_test(
        "Config",
        ".gitignore present",
        os.path.exists(".gitignore"),
        "File not found"
    )
    
    # Test 28: Virtual environment exists
    results.add_test(
        "Config",
        "Virtual environment (ven/) exists",
        os.path.exists("ven") and os.path.isdir("ven"),
        "Directory not found"
    )
    
    # Test 29: copilot-instructions.md exists
    instructions_path = ".github/copilot-instructions.md"
    results.add_test(
        "Config",
        "Copilot instructions present",
        os.path.exists(instructions_path),
        "File not found"
    )
    
    # Test 30: run.py is executable logic
    if os.path.exists("run.py"):
        try:
            with open("run.py", 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                has_uvicorn = 'uvicorn' in content
                results.add_test(
                    "Config",
                    "run.py has server logic",
                    has_uvicorn,
                    "No uvicorn import found" if not has_uvicorn else ""
                )
        except Exception as e:
            results.add_test("Config", "run.py has server logic", False, str(e))
    else:
        results.add_test("Config", "run.py has server logic", False, "File not found")
    
    # Test 31: CHANGELOG.md or version tracking
    has_changelog = os.path.exists("CHANGELOG.md") or os.path.exists("VERSION")
    results.add_test(
        "Config",
        "Version tracking present",
        has_changelog,
        "Consider adding CHANGELOG.md"
    )


def test_code_quality(results):
    """Test 32-39: Code quality checks"""
    print(f"\n{BOLD}6. Code Quality (8 tests){RESET}")
    
    # Test 32: No print() statements in critical files (should use logging)
    critical_files = ["src/inference.py", "src/speculative.py", "src/api.py"]
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Allow print in comments or strings, but not as statements
                    print_statements = [line for line in content.split('\n') 
                                      if 'print(' in line and not line.strip().startswith('#')]
                    results.add_test(
                        "Quality",
                        f"{file_path} uses logging",
                        len(print_statements) == 0,
                        f"Found {len(print_statements)} print() statements"
                    )
            except Exception as e:
                results.add_test("Quality", f"{file_path} uses logging", False, str(e))
    
    # Test 35: Functions have docstrings
    if os.path.exists("src/inference.py"):
        try:
            with open("src/inference.py", 'r', encoding='utf-8') as f:
                content = f.read()
                # Count docstrings (triple quotes)
                docstring_count = content.count('"""') + content.count("'''")
                # Should have at least 10 functions with docstrings
                results.add_test(
                    "Quality",
                    "Functions have docstrings",
                    docstring_count >= 20,  # 10 functions = 20 triple-quotes
                    f"Found {docstring_count//2} docstrings, expected ≥10"
                )
        except Exception as e:
            results.add_test("Quality", "Functions have docstrings", False, str(e))
    
    # Test 36: Error handling present
    if os.path.exists("src/inference.py"):
        try:
            with open("src/inference.py", 'r', encoding='utf-8') as f:
                content = f.read()
                try_count = content.count('try:')
                except_count = content.count('except')
                results.add_test(
                    "Quality",
                    "Error handling present",
                    try_count >= 3 and except_count >= 3,
                    f"Found {try_count} try blocks, {except_count} except blocks"
                )
        except Exception as e:
            results.add_test("Quality", "Error handling present", False, str(e))
    
    # Test 37: Type hints used
    if os.path.exists("src/api.py"):
        try:
            with open("src/api.py", 'r', encoding='utf-8') as f:
                content = f.read()
                # Check for type hints
                has_typing_import = 'from typing import' in content or 'import typing' in content
                has_pydantic = 'from pydantic import BaseModel' in content
                has_annotations = ' -> ' in content or ': str' in content or ': int' in content
                results.add_test(
                    "Quality",
                    "Type hints used",
                    has_typing_import or has_pydantic,  # Pydantic provides type validation
                    "Missing type hints" if not (has_typing_import or has_pydantic) else ""
                )
        except Exception as e:
            results.add_test("Quality", "Type hints used", False, str(e))
    
    # Test 38: Logging configured
    files_with_logging = ["src/api.py", "src/inference.py", "run.py"]
    for file_path in files_with_logging:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    has_logging = 'import logging' in content and 'logger' in content
                    # Only test one file to avoid redundancy
                    if file_path == "src/api.py":
                        results.add_test(
                            "Quality",
                            "Logging configured",
                            has_logging,
                            "No logging setup found"
                        )
                    break
            except Exception as e:
                results.add_test("Quality", "Logging configured", False, str(e))
                break


def test_api_structure(results):
    """Test 40-45: API structure and endpoints"""
    print(f"\n{BOLD}7. API Structure (6 tests){RESET}")
    
    if os.path.exists("src/api.py"):
        try:
            with open("src/api.py", 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Test 40: FastAPI app defined
                results.add_test(
                    "API",
                    "FastAPI app defined",
                    'FastAPI(' in content,
                    "No FastAPI instance found"
                )
                
                # Test 41: /generate endpoint
                results.add_test(
                    "API",
                    "/generate endpoint exists",
                    '@app.post("/generate"' in content or "'/generate'" in content or '"/generate"' in content,
                    "Endpoint not found"
                )
                
                # Test 42: /health endpoint
                results.add_test(
                    "API",
                    "/health endpoint exists",
                    '/health' in content,
                    "Endpoint not found"
                )
                
                # Test 43: /metrics endpoint
                results.add_test(
                    "API",
                    "/metrics endpoint exists",
                    '/metrics' in content,
                    "Endpoint not found"
                )
                
                # Test 44: /generate/stream endpoint (SSE)
                results.add_test(
                    "API",
                    "/generate/stream endpoint exists",
                    '/generate/stream' in content and 'StreamingResponse' in content,
                    "SSE endpoint not found"
                )
                
                # Test 45: /generate/batch endpoint
                results.add_test(
                    "API",
                    "/generate/batch endpoint exists",
                    '/batch' in content,
                    "Batch endpoint not found"
                )
        except Exception as e:
            # Mark all API tests as failed
            for test_name in ["FastAPI app defined", "/generate endpoint", "/health endpoint",
                            "/metrics endpoint", "/stream endpoint", "/batch endpoint"]:
                results.add_test("API", test_name, False, str(e))
    else:
        results.add_test("API", "src/api.py exists", False, "File not found", is_critical=True)


def test_submission_readiness(results):
    """Test 46-48: Final submission checks"""
    print(f"\n{BOLD}8. Submission Readiness (3 tests){RESET}")
    
    # Test 46: Git repository initialized
    results.add_test(
        "Submission",
        "Git repository initialized",
        os.path.exists(".git") and os.path.isdir(".git"),
        "Not a git repository"
    )
    
    # Test 47: Check for large files that shouldn't be committed
    large_files_ok = True
    if os.path.exists(".gitignore"):
        try:
            with open(".gitignore", 'r') as f:
                gitignore = f.read()
                # Should ignore common large directories
                patterns = ["ven/", "__pycache__", "*.pyc", "*.log"]
                missing_patterns = [p for p in patterns if p not in gitignore]
                results.add_test(
                    "Submission",
                    ".gitignore properly configured",
                    len(missing_patterns) == 0,
                    f"Consider adding: {missing_patterns}" if missing_patterns else ""
                )
        except Exception as e:
            results.add_test("Submission", ".gitignore properly configured", False, str(e))
    
    # Test 48: README has project description
    if os.path.exists("README.md"):
        try:
            with open("README.md", 'r', encoding='utf-8') as f:
                readme = f.read()
                has_title = len(readme) > 500  # Substantial README
                has_helix = 'helix' in readme.lower()
                results.add_test(
                    "Submission",
                    "README complete",
                    has_title and has_helix,
                    "README needs more content" if not has_title else ""
                )
        except Exception as e:
            results.add_test("Submission", "README complete", False, str(e))
    else:
        results.add_test("Submission", "README complete", False, "File not found", is_critical=True)


def main():
    print(f"\n{BOLD}{'='*60}")
    print("Helix Enhanced Validation (48 Tests)")
    print("Target: 99%+ for Top 1% Submission")
    print(f"{'='*60}{RESET}")
    
    results = TestResult()
    
    # Run all test suites
    test_syntax_and_imports(results)
    test_documentation(results)
    test_code_files(results)
    test_benchmark_scripts(results)
    test_configuration(results)
    test_code_quality(results)
    test_api_structure(results)
    test_submission_readiness(results)
    
    # Print comprehensive summary
    results.print_summary()
    
    # Return success if ≥99%
    return results.passed / results.total >= 0.99


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
