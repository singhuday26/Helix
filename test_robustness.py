"""
Comprehensive Test Suite for Helix Robustness
Tests error handling, edge cases, and defensive programming
"""

import sys
import pytest
from typing import List

def test_imports():
    """Test all critical imports work"""
    from src.model_loader import ModelPair, get_device
    from src.inference import HelixEngine, GenerationConfig
    from src.batch_optimizer import batch_speculative_generate
    from src.api import app
    print("✓ All imports successful")

def test_input_validation():
    """Test input validation and error handling"""
    from src.inference import HelixEngine, GenerationConfig
    
    engine = HelixEngine()
    
    # Test empty prompt
    try:
        engine.generate("", GenerationConfig())
        print("✗ Should have raised ValueError for empty prompt")
        sys.exit(1)
    except ValueError as e:
        print(f"✓ Caught empty prompt error: {e}")
    
    # Test invalid config
    try:
        config = GenerationConfig(max_tokens=-1)
        engine.generate("test", config)
        print("✗ Should have raised ValueError for negative max_tokens")
        sys.exit(1)
    except ValueError as e:
        print(f"✓ Caught invalid max_tokens: {e}")
    
    # Test empty batch
    try:
        engine.batch_generate([])
        print("✗ Should have raised ValueError for empty batch")
        sys.exit(1)
    except ValueError as e:
        print(f"✓ Caught empty batch error: {e}")
    
    # Test batch with empty strings
    try:
        engine.batch_generate(["", "  ", "\n"])
        print("✗ Should have raised ValueError for all-empty batch")
        sys.exit(1)
    except ValueError as e:
        print(f"✓ Caught all-empty batch error: {e}")

def test_device_detection():
    """Test device detection works correctly"""
    from src.model_loader import get_device
    
    device = get_device()
    valid_devices = ['privateuseone', 'cuda', 'mps', 'cpu']
    
    if device in valid_devices:
        print(f"✓ Device detection: {device}")
    else:
        print(f"✗ Unexpected device: {device}")
        sys.exit(1)

def test_model_initialization():
    """Test model initialization with different configs"""
    from src.model_loader import ModelPair
    
    # Test default initialization
    model_pair = ModelPair()
    print(f"✓ Default ModelPair: draft={model_pair.draft_model_id}")
    
    # Test custom initialization
    model_pair2 = ModelPair(
        draft_model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        target_model_id=None  # Demo mode
    )
    print(f"✓ Custom ModelPair initialized")

def test_generation_config():
    """Test GenerationConfig validation"""
    from src.inference import GenerationConfig
    
    # Valid config
    config = GenerationConfig(max_tokens=50, temperature=0.7)
    print("✓ Valid GenerationConfig created")
    
    # Test defaults
    config_default = GenerationConfig()
    assert config_default.temperature > 0
    assert config_default.speculation_depth >= 1
    print("✓ Default GenerationConfig has valid values")

def test_api_models():
    """Test API request/response models"""
    from src.api import GenerateRequest, GenerateResponse, BatchGenerateRequest
    
    # Test GenerateRequest
    req = GenerateRequest(
        prompt="Test prompt",
        max_tokens=50,
        temperature=0.7
    )
    print("✓ GenerateRequest model works")
    
    # Test validation
    try:
        invalid_req = GenerateRequest(
            prompt="",  # Empty prompt should fail validation
            max_tokens=50
        )
        print("✗ Should have failed validation for empty prompt")
    except Exception as e:
        print(f"✓ API validation caught empty prompt: {type(e).__name__}")
    
    # Test BatchGenerateRequest
    batch_req = BatchGenerateRequest(
        prompts=["Test 1", "Test 2"],
        max_tokens=30
    )
    print("✓ BatchGenerateRequest model works")

def test_error_recovery():
    """Test that errors are handled gracefully"""
    from src.inference import HelixEngine
    
    engine = HelixEngine()
    
    # Test that engine can handle multiple error conditions
    test_cases = [
        ("", "empty prompt"),
        ("   ", "whitespace-only prompt"),
    ]
    
    for prompt, description in test_cases:
        try:
            engine.generate(prompt)
            print(f"✗ Should have caught: {description}")
        except ValueError:
            print(f"✓ Handled: {description}")

def test_batch_optimizer_validation():
    """Test batch optimizer input validation"""
    # We can't easily test this without models, but we can check the signature
    from src.batch_optimizer import batch_speculative_generate
    import inspect
    
    sig = inspect.signature(batch_speculative_generate)
    params = list(sig.parameters.keys())
    
    required_params = ['draft_model', 'target_model', 'tokenizer', 'prompts']
    for param in required_params:
        if param not in params:
            print(f"✗ Missing required parameter: {param}")
            sys.exit(1)
    
    print(f"✓ Batch optimizer has all required parameters: {params}")

def test_data_model_consistency():
    """Test that GenerationResult matches API response models"""
    from src.inference import GenerationResult
    from src.api import GenerateResponse
    from dataclasses import fields
    
    # Get fields from GenerationResult
    result_fields = {f.name for f in fields(GenerationResult)}
    
    # Check critical fields exist
    critical_fields = ['text', 'prompt', 'generated_text', 'tokens_generated', 
                      'time_seconds', 'tokens_per_second', 'time_to_first_token']
    
    missing = set(critical_fields) - result_fields
    if missing:
        print(f"✗ Missing critical fields in GenerationResult: {missing}")
        sys.exit(1)
    
    print(f"✓ GenerationResult has all critical fields")

def main():
    print("\n" + "="*60)
    print("Helix Robustness Test Suite")
    print("="*60 + "\n")
    
    tests = [
        ("Imports", test_imports),
        ("Input Validation", test_input_validation),
        ("Device Detection", test_device_detection),
        ("Model Initialization", test_model_initialization),
        ("Generation Config", test_generation_config),
        ("API Models", test_api_models),
        ("Error Recovery", test_error_recovery),
        ("Batch Optimizer Validation", test_batch_optimizer_validation),
        ("Data Model Consistency", test_data_model_consistency),
    ]
    
    passed = 0
    for name, test_func in tests:
        print(f"\n{'─'*60}")
        print(f"Testing: {name}")
        print(f"{'─'*60}")
        try:
            test_func()
            passed += 1
            print(f"✓ {name} PASSED\n")
        except Exception as e:
            print(f"✗ {name} FAILED: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{len(tests)} tests passed")
    print("="*60 + "\n")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
