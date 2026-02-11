"""
Test script for PagedAttention Memory Comparison Feature

This script tests the new /compare/memory endpoint and validates
the integration between backend and frontend for memory visualization.

Usage:
    1. Start the backend server: python run.py
    2. Run this test: python test_paged_attention_comparison.py
"""

import requests
import json
import sys


def test_memory_comparison_endpoint():
    """Test the /compare/memory endpoint."""
    print("=" * 60)
    print("Testing PagedAttention Memory Comparison Endpoint")
    print("=" * 60)
    
    url = "http://localhost:8000/compare/memory"
    
    try:
        print(f"\n📡 Sending GET request to {url}...")
        response = requests.get(url, timeout=10)
        
        print(f"✓ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✓ Response received successfully!\n")
            
            # Display the memory comparison data
            print("📊 Memory Comparison Results:")
            print("-" * 60)
            print(f"  Traditional KV Cache: {data['traditional_memory_mb']:.2f} MB")
            print(f"  PagedAttention Cache:  {data['paged_memory_mb']:.2f} MB")
            print(f"  Memory Saved:          {data['memory_saved_mb']:.2f} MB ({data['memory_saved_percent']:.1f}%)")
            print(f"\n📦 Block Statistics:")
            print(f"  Total Blocks:          {data['num_blocks']}")
            print(f"  Block Size:            {data['block_size']} tokens")
            print(f"  Blocks Used:           {data['blocks_used']}")
            print(f"  Blocks Free:           {data['blocks_free']}")
            print(f"  Utilization:           {data['utilization_percent']:.1f}%")
            print(f"  Sequence Length:       {data['sequence_length']} tokens")
            print("-" * 60)
            
            # Validate data integrity
            print("\n🔍 Validating Data Integrity:")
            
            # Check that memory saved is correct
            calculated_saved = data['traditional_memory_mb'] - data['paged_memory_mb']
            if abs(calculated_saved - data['memory_saved_mb']) < 0.01:
                print("  ✓ Memory saved calculation is correct")
            else:
                print(f"  ✗ Memory saved mismatch: expected {calculated_saved}, got {data['memory_saved_mb']}")
            
            # Check that blocks used + blocks free = total blocks
            if data['blocks_used'] + data['blocks_free'] == data['num_blocks']:
                print("  ✓ Block count is correct")
            else:
                print(f"  ✗ Block count mismatch")
            
            # Check that utilization calculation is correct
            calculated_util = (data['blocks_used'] / data['num_blocks']) * 100
            if abs(calculated_util - data['utilization_percent']) < 0.1:
                print("  ✓ Utilization percentage is correct")
            else:
                print(f"  ✗ Utilization mismatch: expected {calculated_util}, got {data['utilization_percent']}")
            
            print("\n✅ All tests passed!")
            return True
        else:
            print(f"\n❌ Error: Server returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server")
        print("   Make sure the backend server is running: python run.py")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def test_api_documentation():
    """Test if the endpoint appears in API docs."""
    print("\n" + "=" * 60)
    print("Testing API Documentation")
    print("=" * 60)
    
    try:
        # Test OpenAPI schema
        response = requests.get("http://localhost:8000/openapi.json", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            if "/compare/memory" in schema.get("paths", {}):
                print("✓ /compare/memory endpoint is documented in OpenAPI schema")
                print("  View docs at: http://localhost:8000/docs")
                print("  View redoc at: http://localhost:8000/redoc")
                return True
            else:
                print("✗ Endpoint not found in OpenAPI schema")
                return False
        else:
            print(f"✗ Could not fetch OpenAPI schema (status {response.status_code})")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_cors():
    """Test CORS headers for frontend access."""
    print("\n" + "=" * 60)
    print("Testing CORS Configuration")
    print("=" * 60)
    
    try:
        response = requests.get(
            "http://localhost:8000/compare/memory",
            headers={"Origin": "http://localhost:5173"},  # Frontend origin
            timeout=5
        )
        
        cors_header = response.headers.get("Access-Control-Allow-Origin")
        if cors_header:
            print(f"✓ CORS enabled: {cors_header}")
            return True
        else:
            print("✗ CORS header not found")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n🧪 PagedAttention Comparison Feature Test Suite\n")
    
    results = {
        "Memory Comparison Endpoint": test_memory_comparison_endpoint(),
        "API Documentation": test_api_documentation(),
        "CORS Configuration": test_cors(),
    }
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! The feature is ready to use.")
        print("\nNext steps:")
        print("  1. Open http://localhost:5173/comparison in your browser")
        print("  2. Click 'Show Memory Comparison' button")
        print("  3. Observe the animated memory block visualization")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the backend server.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
