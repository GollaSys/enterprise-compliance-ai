#!/usr/bin/env python3
"""
Complete test suite for Enterprise Compliance AI Platform
Tests all features and use cases
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List
import asyncio

BASE_URL = "http://localhost:8001"

class ComplianceTestSuite:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_results = []
        self.compliance_id = None
        self.document_ids = []
        self.report_id = None

    def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 60)
        print("ENTERPRISE COMPLIANCE AI - COMPLETE TEST SUITE")
        print("=" * 60)
        print()

        tests = [
            ("System Health", self.test_health),
            ("Document Upload", self.test_document_upload),
            ("Policy Management", self.test_policies),
            ("Compliance Analysis", self.test_compliance_analysis),
            ("Dashboard Metrics", self.test_dashboard),
            ("Risk Assessment", self.test_risk_assessment),
            ("Evidence Validation", self.test_evidence_validation),
            ("Gap Analysis", self.test_gap_analysis),
            ("Agent Status", self.test_agents),
            ("Report Generation", self.test_reports),
            ("Complete Workflow", self.test_complete_workflow),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            print(f"\nTesting: {test_name}")
            print("-" * 40)
            try:
                test_func()
                print(f"✅ {test_name} - PASSED")
                passed += 1
            except AssertionError as e:
                print(f"❌ {test_name} - FAILED: {str(e)}")
                failed += 1
            except Exception as e:
                print(f"❌ {test_name} - ERROR: {str(e)}")
                failed += 1

        print("\n" + "=" * 60)
        print(f"TEST RESULTS: {passed} passed, {failed} failed")
        print("=" * 60)

        return failed == 0

    def test_health(self):
        """Test system health endpoints"""
        # Test root endpoint
        response = requests.get(f"{self.base_url}/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        print(f"  • System status: {data['status']}")

        # Test health endpoint
        response = requests.get(f"{self.base_url}/health")
        assert response.status_code == 200
        health = response.json()
        assert health["status"] == "healthy"
        print(f"  • Health check: {health['status']}")
        print(f"  • Services: {list(health['services'].keys())}")

    def test_dashboard(self):
        """Test dashboard metrics (runs after compliance analysis populates data)"""
        response = requests.get(f"{self.base_url}/api/v1/dashboard/metrics")
        assert response.status_code == 200
        metrics = response.json()

        assert "overall_compliance" in metrics
        assert "active_risks" in metrics
        assert "open_gaps" in metrics
        assert "audit_readiness" in metrics
        assert metrics["overall_compliance"] > 0, "Compliance score should be > 0 after analysis"
        assert metrics["active_risks"] > 0, "Risks should exist after compliance analysis"
        print(f"  • Overall compliance: {metrics['overall_compliance']}%")
        print(f"  • Active risks: {metrics['active_risks']}")
        print(f"  • Open gaps: {metrics['open_gaps']}")
        print(f"  • Audit readiness: {metrics['audit_readiness']}%")

        # Test activities — should have entries from prior tests
        response = requests.get(f"{self.base_url}/api/v1/dashboard/activities")
        assert response.status_code == 200
        activities = response.json()
        assert "activities" in activities
        assert len(activities["activities"]) > 0, "Activities should exist from prior actions"
        print(f"  • Recent activities: {len(activities['activities'])}")

    def test_document_upload(self):
        """Test document management"""
        # Upload test document
        files = {
            'file': ('test_compliance.txt', b'Test compliance document content for analysis', 'text/plain')
        }
        response = requests.post(
            f"{self.base_url}/api/v1/documents/upload",
            files=files,
            data={'doc_type': 'policy'}
        )
        assert response.status_code == 200
        doc = response.json()
        self.document_ids.append(doc['document_id'])
        print(f"  • Document uploaded: {doc['document_id']}")

        # List documents
        response = requests.get(f"{self.base_url}/api/v1/documents")
        assert response.status_code == 200
        docs = response.json()
        assert docs["total"] >= 1
        print(f"  • Total documents: {docs['total']}")

    def test_policies(self):
        """Test policy management"""
        # List policies
        response = requests.get(f"{self.base_url}/api/v1/policies")
        assert response.status_code == 200
        policies = response.json()
        print(f"  • Policies found: {len(policies['policies'])}")

        # Create new policy
        policy_data = {
            "name": "Data Protection Policy",
            "content": "This policy governs data protection practices...",
            "version": "1.0"
        }
        response = requests.post(
            f"{self.base_url}/api/v1/policies",
            params=policy_data
        )
        assert response.status_code == 200
        policy = response.json()
        print(f"  • Policy created: {policy['policy_id']}")

    def test_compliance_analysis(self):
        """Test compliance analysis workflow"""
        # Start analysis
        analysis_data = {
            "regulation_type": "GDPR",
            "document_ids": self.document_ids if self.document_ids else ["DOC-001"],
            "policy_ids": ["POL-001"],
            "include_evidence": True,
            "generate_report": True
        }

        response = requests.post(
            f"{self.base_url}/api/v1/compliance/analyze",
            json=analysis_data
        )
        assert response.status_code == 200
        result = response.json()
        self.compliance_id = result["compliance_id"]
        print(f"  • Analysis started: {self.compliance_id}")

        # Check status
        time.sleep(2)  # Wait for processing
        response = requests.get(
            f"{self.base_url}/api/v1/compliance/status/{self.compliance_id}"
        )
        assert response.status_code == 200
        status = response.json()
        print(f"  • Analysis status: {status['status']}")

        # Get results (may need to wait)
        max_attempts = 5
        for _ in range(max_attempts):
            response = requests.get(
                f"{self.base_url}/api/v1/compliance/results/{self.compliance_id}"
            )
            if response.status_code == 200:
                results = response.json()
                if results and "results" in results:
                    print(f"  • Compliance score: {results['results']['compliance_score']}%")
                    print(f"  • Gaps identified: {len(results['results']['gaps'])}")
                    print(f"  • Risks found: {len(results['results']['risks'])}")
                    break
            time.sleep(2)

    def test_risk_assessment(self):
        """Test risk assessment features"""
        # List risks
        response = requests.get(f"{self.base_url}/api/v1/risks")
        assert response.status_code == 200
        risks = response.json()
        print(f"  • Active risks: {risks['total']}")

        # Assess specific risks
        response = requests.post(
            f"{self.base_url}/api/v1/risks/assess",
            json=["GAP-001", "GAP-002"]
        )
        assert response.status_code == 200
        assessment = response.json()
        print(f"  • Risk assessments: {len(assessment['assessments'])}")
        print(f"  • Total risk score: {assessment['total_risk_score']}")

    def test_evidence_validation(self):
        """Test evidence validation"""
        validation_data = {
            "evidence_ids": ["EVD-001", "EVD-002"],
            "requirements": ["REQ-001", "REQ-002"]
        }

        response = requests.post(
            f"{self.base_url}/api/v1/evidence/validate",
            json=validation_data
        )
        assert response.status_code == 200
        validation = response.json()
        print(f"  • Evidence validated: {validation['total_validated']}")
        print(f"  • Overall validity: {validation['overall_validity']}")

    def test_gap_analysis(self):
        """Test gap analysis"""
        gap_data = {
            "regulation_ids": ["GDPR", "SOX"],
            "policy_ids": ["POL-001", "POL-002"]
        }

        response = requests.post(
            f"{self.base_url}/api/v1/gaps/analyze",
            json=gap_data
        )
        assert response.status_code == 200
        gaps = response.json()
        print(f"  • Total gaps: {gaps['total_gaps']}")
        print(f"  • Critical gaps: {gaps['critical_gaps']}")
        print(f"  • Coverage score: {gaps['coverage_score']}")

    def test_agents(self):
        """Test agent management"""
        # Get agent status
        response = requests.get(f"{self.base_url}/api/v1/agents/status")
        assert response.status_code == 200
        agents = response.json()
        print(f"  • Active agents: {len(agents)}")

        for agent in agents:
            print(f"    - {agent['name']}: {agent['status']}")

        # Execute agent task
        task_data = {
            "task_type": "analyze",
            "content": "Test content for analysis"
        }
        response = requests.post(
            f"{self.base_url}/api/v1/agents/regulatory_analyst/execute",
            json=task_data
        )
        assert response.status_code == 200
        print(f"  • Agent task executed successfully")

    def test_reports(self):
        """Test report generation"""
        # Generate report
        report_data = {
            "report_type": "executive_summary",
            "period": "Q4 2024",
            "include_charts": True,
            "format": "pdf"
        }

        response = requests.post(
            f"{self.base_url}/api/v1/reports/generate",
            json=report_data
        )
        assert response.status_code == 200
        report = response.json()
        self.report_id = report["report_id"]
        print(f"  • Report generation started: {self.report_id}")

        # List reports
        response = requests.get(f"{self.base_url}/api/v1/reports")
        assert response.status_code == 200
        reports = response.json()
        print(f"  • Total reports: {len(reports['reports'])}")

    def test_complete_workflow(self):
        """Test complete compliance workflow"""
        print("  Running complete workflow test...")

        # 1. Upload document
        files = {'file': ('workflow_test.txt', b'Workflow test document', 'text/plain')}
        response = requests.post(f"{self.base_url}/api/v1/documents/upload", files=files)
        assert response.status_code == 200
        doc_id = response.json()["document_id"]
        print(f"  • Step 1: Document uploaded ({doc_id})")

        # 2. Create policy
        policy_data = {"name": "Test Policy", "content": "Policy content", "version": "1.0"}
        response = requests.post(f"{self.base_url}/api/v1/policies", params=policy_data)
        assert response.status_code == 200
        policy_id = response.json()["policy_id"]
        print(f"  • Step 2: Policy created ({policy_id})")

        # 3. Run compliance analysis
        analysis_data = {
            "regulation_type": "GDPR",
            "document_ids": [doc_id],
            "policy_ids": [policy_id]
        }
        response = requests.post(f"{self.base_url}/api/v1/compliance/analyze", json=analysis_data)
        assert response.status_code == 200
        compliance_id = response.json()["compliance_id"]
        print(f"  • Step 3: Analysis initiated ({compliance_id})")

        # 4. Generate report
        report_data = {"report_type": "compliance_assessment", "period": "Current"}
        response = requests.post(f"{self.base_url}/api/v1/reports/generate", json=report_data)
        assert response.status_code == 200
        report_id = response.json()["report_id"]
        print(f"  • Step 4: Report generated ({report_id})")

        print("  • Complete workflow executed successfully!")

    def test_regulations(self):
        """Test regulation endpoints"""
        response = requests.get(f"{self.base_url}/api/v1/regulations")
        assert response.status_code == 200
        regulations = response.json()
        assert len(regulations["regulations"]) > 0
        print(f"  • Available regulations: {len(regulations['regulations'])}")
        for reg in regulations["regulations"]:
            print(f"    - {reg['name']}: {reg['requirements']} requirements")


def main():
    """Main test runner"""
    print("\nChecking if API is running...")

    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ API is not responding correctly")
            print("Please ensure the backend is running on port 8001")
            return 1
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API at http://localhost:8001")
        print("Please start the backend first:")
        print("  docker-compose up -d")
        print("  OR")
        print("  python -m uvicorn src.api.main:app --port 8001")
        return 1

    # Run test suite
    test_suite = ComplianceTestSuite()
    success = test_suite.run_all_tests()

    if success:
        print("\n✅ ALL TESTS PASSED! Platform is fully operational.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())