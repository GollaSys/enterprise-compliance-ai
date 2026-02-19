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
    data = response.json()
    assert data["status"] == "healthy"
    print(f"  Health check: {data['status']}")
    print(f"  Services: {list(data['services'].keys())}")

def test_dashboard():
    """Test dashboard metrics"""
    print("\nTesting dashboard endpoints...")

    # Test metrics
    response = requests.get(f"{BASE_URL}/api/v1/dashboard/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert "overall_compliance" in metrics
    print(f"  Dashboard metrics - Compliance: {metrics['overall_compliance']}%")

    # Test activities
    response = requests.get(f"{BASE_URL}/api/v1/dashboard/activities")
    assert response.status_code == 200
    activities = response.json()
    print(f"  Recent activities: {len(activities['activities'])} items")

def test_compliance():
    """Test compliance analysis"""
    print("\nTesting compliance endpoints...")

    # Get regulations
    response = requests.get(f"{BASE_URL}/api/v1/compliance/regulations")
    assert response.status_code == 200
    regulations = response.json()
    print(f"  Available regulations: {len(regulations['regulations'])}")

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
    compliance_id = result["compliance_id"]
    print(f"  Analysis started: {compliance_id}")
    print(f"  Compliance score: {result['results']['compliance_score']}%")
    print(f"  Gaps found: {len(result['results']['gaps'])}")
    print(f"  Risks identified: {len(result['results']['risks'])}")

    # Check status
    response = requests.get(f"{BASE_URL}/api/v1/compliance/status/{compliance_id}")
    assert response.status_code == 200
    status = response.json()
    print(f"  Status check: {status['status']}")

    # Get full results
    response = requests.get(f"{BASE_URL}/api/v1/compliance/results/{compliance_id}")
    assert response.status_code == 200
    print(f"  Results retrieved successfully")

def test_documents():
    """Test document endpoints"""
    print("\nTesting document endpoints...")

    # List documents
    response = requests.get(f"{BASE_URL}/api/v1/documents")
    assert response.status_code == 200
    docs = response.json()
    print(f"  Documents in system: {docs['total']}")

    # Upload test document
    files = {
        'file': ('test.txt', b'Test compliance document content', 'text/plain')
    }
    response = requests.post(f"{BASE_URL}/api/v1/documents/upload", files=files)
    assert response.status_code == 200
    doc = response.json()
    print(f"  Document uploaded: {doc['document_id']}")

def test_agents():
    """Test agent status"""
    print("\nTesting agent endpoints...")

    response = requests.get(f"{BASE_URL}/api/v1/agents/status")
    assert response.status_code == 200
    agents = response.json()
    print(f"  Active agents: {len(agents)}")
    for agent in agents:
        print(f"    - {agent['name']}: {agent['status']} ({agent['tasks_completed']} tasks)")

    # Execute agent task
    task_data = {"task_type": "analyze", "content": "Test content"}
    response = requests.post(
        f"{BASE_URL}/api/v1/agents/regulatory_analyst/execute",
        json=task_data
    )
    assert response.status_code == 200
    print(f"  Agent task executed successfully")

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
        json=report_data
    )
    assert response.status_code == 200
    report = response.json()
    print(f"  Report generated: {report['report_id']}")

    # List reports
    response = requests.get(f"{BASE_URL}/api/v1/reports")
    assert response.status_code == 200
    reports = response.json()
    print(f"  Total reports: {reports['total']}")

def test_policies():
    """Test policy management"""
    print("\nTesting policy endpoints...")

    # Create policy
    response = requests.post(
        f"{BASE_URL}/api/v1/policies",
        params={"name": "Test Policy", "content": "Test content", "version": "1.0"}
    )
    assert response.status_code == 200
    policy = response.json()
    print(f"  Policy created: {policy['policy_id']}")

    # List policies
    response = requests.get(f"{BASE_URL}/api/v1/policies")
    assert response.status_code == 200
    policies = response.json()
    print(f"  Total policies: {len(policies['policies'])}")

def test_risks():
    """Test risk management"""
    print("\nTesting risk endpoints...")

    # List risks
    response = requests.get(f"{BASE_URL}/api/v1/risks")
    assert response.status_code == 200
    risks = response.json()
    print(f"  Active risks: {risks['total']}")

    # Assess risks
    response = requests.post(
        f"{BASE_URL}/api/v1/risks/assess",
        json=["GAP-001", "GAP-002"]
    )
    assert response.status_code == 200
    assessment = response.json()
    print(f"  Assessments: {len(assessment['assessments'])}")
    print(f"  Total risk score: {assessment['total_risk_score']}")

def test_evidence():
    """Test evidence validation"""
    print("\nTesting evidence endpoints...")

    response = requests.post(
        f"{BASE_URL}/api/v1/evidence/validate",
        json={"evidence_ids": ["EVD-001", "EVD-002"], "requirements": ["REQ-001"]}
    )
    assert response.status_code == 200
    result = response.json()
    print(f"  Evidence validated: {result['total_validated']}")
    print(f"  Overall validity: {result['overall_validity']}")

def test_gaps():
    """Test gap analysis"""
    print("\nTesting gap analysis endpoints...")

    response = requests.post(
        f"{BASE_URL}/api/v1/gaps/analyze",
        json={"regulation_ids": ["GDPR", "SOX"], "policy_ids": ["POL-001"]}
    )
    assert response.status_code == 200
    result = response.json()
    print(f"  Total gaps: {result['total_gaps']}")
    print(f"  Critical gaps: {result['critical_gaps']}")
    print(f"  Coverage score: {result['coverage_score']}")

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
        test_policies()
        test_risks()
        test_evidence()
        test_gaps()

        print("\n" + "=" * 50)
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 50)

    except AssertionError as e:
        print(f"\nTest failed: {e}")
        return False
    except requests.exceptions.ConnectionError:
        print("\nCannot connect to API. Make sure the server is running on port 8001")
        return False
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
