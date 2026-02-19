#!/usr/bin/env python3
"""
Test script to verify all API endpoints are working
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print(f"✅ Health check: {response.json()}")

def test_dashboard():
    """Test dashboard metrics"""
    print("\nTesting dashboard endpoints...")

    # Test metrics
    response = requests.get(f"{BASE_URL}/api/v1/dashboard/metrics")
    assert response.status_code == 200
    metrics = response.json()
    print(f"✅ Dashboard metrics - Compliance: {metrics['overall_compliance']}%")

    # Test activities
    response = requests.get(f"{BASE_URL}/api/v1/dashboard/activities")
    assert response.status_code == 200
    activities = response.json()
    print(f"✅ Recent activities: {len(activities['activities'])} items")

def test_compliance():
    """Test compliance analysis"""
    print("\nTesting compliance endpoints...")

    # Get regulations
    response = requests.get(f"{BASE_URL}/api/v1/compliance/regulations")
    assert response.status_code == 200
    regulations = response.json()
    print(f"✅ Available regulations: {len(regulations['regulations'])}")

    # Run analysis
    analysis_data = {
        "regulation_type": "GDPR",
        "document_ids": ["DOC-001", "DOC-002"]
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/compliance/analyze",
        json=analysis_data
    )
    assert response.status_code == 200
    result = response.json()
    print(f"✅ Compliance analysis - Score: {result['compliance_score']}%")
    print(f"   - Gaps found: {len(result['gaps'])}")
    print(f"   - Risks identified: {len(result['risks'])}")

def test_documents():
    """Test document endpoints"""
    print("\nTesting document endpoints...")

    # List documents
    response = requests.get(f"{BASE_URL}/api/v1/documents")
    assert response.status_code == 200
    docs = response.json()
    print(f"✅ Documents in system: {docs['total']}")

    # Upload test document
    files = {
        'file': ('test.txt', b'Test compliance document content', 'text/plain')
    }
    response = requests.post(f"{BASE_URL}/api/v1/documents/upload", files=files)
    assert response.status_code == 200
    doc = response.json()
    print(f"✅ Document uploaded: {doc['document']['id']}")

def test_agents():
    """Test agent status"""
    print("\nTesting agent endpoints...")

    response = requests.get(f"{BASE_URL}/api/v1/agents/status")
    assert response.status_code == 200
    status = response.json()
    print(f"✅ Agent system status: {status['overall_status']}")
    for agent in status['agents']:
        print(f"   - {agent['name']}: {agent['status']} ({agent['tasks_completed']} tasks)")

def test_reports():
    """Test report generation"""
    print("\nTesting report endpoints...")

    # Generate report
    report_data = {
        "report_type": "executive_summary",
        "period": "Q4 2024"
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/reports/generate",
        params=report_data  # Using params instead of json for query parameters
    )
    assert response.status_code == 200
    report = response.json()
    print(f"✅ Report generated: {report['id']}")

    # List reports
    response = requests.get(f"{BASE_URL}/api/v1/reports")
    assert response.status_code == 200
    reports = response.json()
    print(f"✅ Total reports: {reports['total']}")

def run_all_tests():
    """Run all API tests"""
    print("=" * 50)
    print("COMPLIANCE AI PLATFORM - API TEST SUITE")
    print("=" * 50)

    try:
        test_health()
        test_dashboard()
        test_compliance()
        test_documents()
        test_agents()
        test_reports()

        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 50)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to API. Make sure the server is running on port 8001")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

    return True

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)