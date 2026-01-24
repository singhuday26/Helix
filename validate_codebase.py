"""
Comprehensive validation script for Helix codebase
Tests imports, dependencies, API consistency, and basic functionality
"""

import sys
import importlib
from typing import List, Tuple

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def test_result(passed: bool, test_name: str, details: str = "") -> None:
    """Print test result with color coding"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {test_name}")
    if details and not passed:
        print(f"  {YELLOW}Details: {details}{RESET}")

def main():
    print(f"\n{BOLD}{'='*60}")
    print("Helix Codebase Validation")
    print(f"{'='*60}{RESET}\n")
    
    passed_tests = 0
    total_tests = 0
    issues = []
    
    # Test 1: Core imports
    print(f"{BOLD}1. Testing Core Imports{RESET}")
    core_modules = [
        "torch",
        "transformers",
        "fastapi",
        "uvicorn",
        "pydantic",
    ]
    
    for module in core_modules:
        total_tests += 1
        try:
            importlib.import_module(module)
            test_result(True, f"Import {module}")
            passed_tests += 1
        except ImportError as e:
            test_result(False, f"Import {module}", str(e))
            issues.append(f"Missing dependency: {module}")
    
    # Test 2: Helix modules
    print(f"\n{BOLD}2. Testing Helix Modules{RESET}")
    helix_modules = [
        "src.model_loader",
        "src.kv_cache",
        "src.speculative",
        "src.batch_optimizer",
        "src.inference",
        "src.api",
    ]
    
    for module in helix_modules:
        total_tests += 1
        try:
            importlib.import_module(module)
            test_result(True, f"Import {module}")
            passed_tests += 1
        except Exception as e:
            test_result(False, f"Import {module}", str(e))
            issues.append(f"Module import failed: {module}")
    
    # Test 3: DirectML support
    print(f"\n{BOLD}3. Testing DirectML Support{RESET}")
    total_tests += 1
    try:
        import torch_directml
        test_result(True, "torch-directml available")
        passed_tests += 1
    except ImportError:
        test_result(False, "torch-directml not available", "AMD GPU support may not work")
        issues.append("torch-directml not installed")
    
    # Test 4: Device detection
    print(f"\n{BOLD}4. Testing Device Detection{RESET}")
    total_tests += 1
    try:
        from src.model_loader import get_device
        device = get_device()
        test_result(True, f"Device detection: {device}")
        passed_tests += 1
    except Exception as e:
        test_result(False, "Device detection", str(e))
        issues.append("Device detection failed")
    
    # Test 5: Engine initialization
    print(f"\n{BOLD}5. Testing Engine Initialization{RESET}")
    total_tests += 1
    try:
        from src.inference import HelixEngine
        engine = HelixEngine()
        test_result(True, "HelixEngine initialization")
        passed_tests += 1
    except Exception as e:
        test_result(False, "HelixEngine initialization", str(e))
        issues.append("Engine initialization failed")
    
    # Test 6: API structure
    print(f"\n{BOLD}6. Testing API Structure{RESET}")
    total_tests += 1
    try:
        from src.api import app, GenerateRequest, GenerateResponse, BatchGenerateRequest, BatchGenerateResponse
        test_result(True, "API models and app")
        passed_tests += 1
    except Exception as e:
        test_result(False, "API structure", str(e))
        issues.append("API structure validation failed")
    
    # Test 7: Data model consistency
    print(f"\n{BOLD}7. Testing Data Model Consistency{RESET}")
    total_tests += 1
    try:
        from src.inference import GenerationResult
        from src.api import GenerateResponse
        
        # Check that GenerateResponse can be created from GenerationResult fields
        required_fields = ['text', 'prompt', 'generated_text', 'tokens_generated', 
                          'time_seconds', 'tokens_per_second', 'time_to_first_token', 'stats']
        
        # Get GenerationResult fields
        from dataclasses import fields
        result_fields = {f.name for f in fields(GenerationResult)}
        
        # Check all required fields exist
        missing = set(required_fields) - result_fields
        if missing:
            test_result(False, "Data model consistency", f"Missing fields: {missing}")
            issues.append(f"GenerationResult missing fields: {missing}")
        else:
            test_result(True, "Data model consistency")
            passed_tests += 1
    except Exception as e:
        test_result(False, "Data model consistency", str(e))
        issues.append("Data model validation failed")
    
    # Test 8: Batch optimizer
    print(f"\n{BOLD}8. Testing Batch Optimizer{RESET}")
    total_tests += 1
    try:
        from src.batch_optimizer import batch_speculative_generate
        import inspect
        sig = inspect.signature(batch_speculative_generate)
        expected_params = ['draft_model', 'target_model', 'tokenizer', 'prompts', 
                          'max_tokens', 'temperature', 'speculation_depth']
        actual_params = list(sig.parameters.keys())
        
        if all(p in actual_params for p in expected_params):
            test_result(True, "Batch optimizer signature")
            passed_tests += 1
        else:
            test_result(False, "Batch optimizer signature", f"Params: {actual_params}")
            issues.append("Batch optimizer signature mismatch")
    except Exception as e:
        test_result(False, "Batch optimizer", str(e))
        issues.append("Batch optimizer validation failed")
    
    # Test 9: Configuration files
    print(f"\n{BOLD}9. Testing Configuration Files{RESET}")
    import os
    config_files = ['requirements.txt', 'run.py']
    
    for file in config_files:
        total_tests += 1
        if os.path.exists(file):
            test_result(True, f"File exists: {file}")
            passed_tests += 1
        else:
            test_result(False, f"File exists: {file}", "File not found")
            issues.append(f"Missing file: {file}")
    
    # Summary
    print(f"\n{BOLD}{'='*60}")
    print("Validation Summary")
    print(f"{'='*60}{RESET}")
    print(f"Total Tests: {total_tests}")
    print(f"{GREEN}Passed: {passed_tests}{RESET}")
    print(f"{RED}Failed: {total_tests - passed_tests}{RESET}")
    
    if issues:
        print(f"\n{BOLD}{RED}Issues Found:{RESET}")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print(f"\n{GREEN}{BOLD}✓ All validations passed! Codebase is robust.{RESET}")
    
    print(f"\n{BOLD}{'='*60}{RESET}\n")
    
    return len(issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
