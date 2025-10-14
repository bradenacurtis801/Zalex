#!/usr/bin/env python3
"""
Simple test to verify the backend classification is working.
"""

import json

import requests


def test_backend_classification():
    """Test the backend classification endpoint."""

    base_url = "http://127.0.0.1:5000"

    print("🧪 Testing Backend Classification")
    print("=" * 40)

    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print(
            "❌ Cannot connect to backend. Make sure it's running on http://127.0.0.1:5000"
        )
        return

    # Test 2: Upload a test PDF
    test_pdf_path = "/Users/bradencurtis/MYWORKSPACE/ScanPro/backend/test_data/es/documents/LicenseCertificate-A8385208.pdf"

    try:
        with open(test_pdf_path, "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}

            print(f"📄 Uploading test PDF: {test_pdf_path}")
            response = requests.post(f"{base_url}/api/upload", files=files)

            if response.status_code == 200:
                result = response.json()
                print("✅ Upload successful!")
                print(f"📋 Response: {json.dumps(result, indent=2)}")

                # Check if classifications are present
                if "classifications" in result and result["classifications"]:
                    print("\n🎯 Classification Results:")
                    for i, classification in enumerate(result["classifications"]):
                        print(f"  {i+1}. {classification['filename']}")
                        print(f"     Category: {classification['category']}")
                        print(f"     Confidence: {classification['confidence']:.3f}")
                else:
                    print("⚠️  No classification results found in response")
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"Error: {response.text}")

    except FileNotFoundError:
        print(f"❌ Test PDF not found: {test_pdf_path}")
    except Exception as e:
        print(f"❌ Error during upload test: {e}")


if __name__ == "__main__":
    test_backend_classification()
