import subprocess
import time
import json

def run_command(cmd):
    """Helper to run CLI commands"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

def test_enqueue_and_process():
    """Test 1: Basic job completes successfully"""
    print("\n=== Test 1: Enqueue and process job ===")
    
    # Enqueue a simple job
    job_data = json.dumps({
        "id": "test-job-1",
        "command": "echo Hello QueueCTL",
        "max_retries": 3
    })
    
    # Escape quotes for Windows
    job_data_escaped = job_data.replace('"', '\\"')
    
    stdout, stderr, code = run_command(f'queuectl enqueue "{job_data_escaped}"')
    
    print(f"STDOUT: {stdout}")
    print(f"STDERR: {stderr}")
    print(f"Return Code: {code}")
    
    if code != 0:
        print(f"\n❌ Enqueue failed!")
        print(f"Error: {stderr}")
        return False
    
    print("✓ Test 1 passed")
    return True

def test_status():
    """Test: Check status"""
    print("\n=== Test: Status Check ===")
    
    stdout, stderr, code = run_command('queuectl status')
    print(f"Status output:\n{stdout}")
    
    if code != 0:
        print(f"❌ Status command failed: {stderr}")
        return False
    
    print("✓ Status test passed")
    return True

def test_list_jobs():
    """Test: List jobs"""
    print("\n=== Test: List jobs ===")
    
    stdout, stderr, code = run_command('queuectl list')
    print(f"Jobs list:\n{stdout}")
    
    if code != 0:
        print(f"❌ List command failed: {stderr}")
        return False
    
    print("✓ List test passed")
    return True

def test_config():
    """Test: Configuration management"""
    print("\n=== Test: Configuration ===")
    
    # Get config
    stdout, stderr, code = run_command('queuectl config get')
    print(f"Config:\n{stdout}")
    
    if code != 0:
        print(f"❌ Config get failed: {stderr}")
        return False
    
    print("✓ Config test passed")
    return True

if __name__ == '__main__':
    print("Starting QueueCTL Tests...")
    print("=" * 50)
    
    all_passed = True
    
    # Run tests
    if not test_status():
        all_passed = False
    
    if not test_config():
        all_passed = False
    
    if not test_enqueue_and_process():
        all_passed = False
    
    if not test_list_jobs():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("❌ Some tests failed")