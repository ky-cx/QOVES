import requests
import json
import time
import base64

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
HEADERS = {"Content-Type": "application/json"}
TEST_TIMEOUT = 45  # seconds

# --- Helper Functions ---
def print_test_header(name):
    print("\n" + "="*50)
    print(f"  🧪 RUNNING TEST: {name}")
    print("="*50)

def print_result(success, message=""):
    if success:
        print("  ✅ PASSED")
    else:
        print(f"  ❌ FAILED: {message}")
    return success

# --- Test Cases ---

def test_prometheus_metrics():
    print_test_header("Prometheus Metrics Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/metrics")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "http_requests_total" in response.text, "Prometheus metrics not found in response"
        return print_result(True)
    except Exception as e:
        return print_result(False, e)

def test_correct_payload_submission():
    print_test_header("Correct Payload Submission")
    try:
        with open("payload.json", "r") as f:
            payload = json.load(f)
        
        response = requests.post(f"{BASE_URL}{API_PREFIX}/submit", headers=HEADERS, json=payload)
        
        assert response.status_code == 202, f"Expected 202, got {response.status_code}"
        data = response.json()
        assert "id" in data and "status" in data, "Response missing 'id' or 'status'"
        assert data["status"] == "pending", "Initial status should be 'pending'"
        
        print(f"  - Job submitted successfully with ID: {data['id']}")
        return print_result(True), data['id']
    except Exception as e:
        return print_result(False, e), None

def test_invalid_payload_submission():
    print_test_header("Invalid Payload Submission (Missing Field)")
    try:
        invalid_payload = {
            "image": "test_string",
            "segmentation_map": "test_string"
        }
        response = requests.post(f"{BASE_URL}{API_PREFIX}/submit", headers=HEADERS, json=invalid_payload)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        return print_result(True)
    except Exception as e:
        return print_result(False, e)

def test_async_workflow(job_id):
    print_test_header(f"Full Asynchronous Workflow for Job ID: {job_id}")
    try:
        start_time = time.time()
        while time.time() - start_time < TEST_TIMEOUT:
            print(f"  - Polling status for job {job_id}...")
            response = requests.get(f"{BASE_URL}{API_PREFIX}/status/{job_id}")
            
            assert response.status_code != 500, f"Server returned an error: {response.text}"
            
            if response.status_code == 200:
                data = response.json()
                assert "svg" in data and "mask_contours" in data, "Final result is missing 'svg' or 'mask_contours'"
                print("  - Job completed and final result received!")
                return print_result(True)
            
            print("  - Job is still pending, waiting 5 seconds...")
            time.sleep(5)
            
        return print_result(False, f"Job did not complete within timeout of {TEST_TIMEOUT}s")
    except Exception as e:
        return print_result(False, e)

# --- Main Test Runner ---
if __name__ == "__main__":
    print("\n--- Starting QOVES API Test Suite ---")
    
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to the API at http://localhost:8000.")
        print("Please ensure your Docker services are running with 'docker-compose up'.")
        exit()

    results = []
    job_id_for_workflow_test = None

    results.append(test_prometheus_metrics())
    results.append(test_invalid_payload_submission())
    
    success, job_id_for_workflow_test = test_correct_payload_submission()
    results.append(success)

    if job_id_for_workflow_test:
        results.append(test_async_workflow(job_id_for_workflow_test))
    
    print("\n" + "="*50)
    print("  📊 TEST SUITE SUMMARY")
    print("="*50)
    if all(results):
        print("\n  🎉 All tests passed successfully! 🎉")
    else:
        print(f"\n  🔥 Some tests failed. ({results.count(False)} out of {len(results)} failed)")
    print()