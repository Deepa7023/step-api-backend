#!/usr/bin/env python3
"""
Test script for STEP File Analysis API
Demonstrates how to use the API endpoints
"""

import requests
import json
import sys
from pathlib import Path


class STEPAPIClient:
    """Client for interacting with STEP API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def health_check(self):
        """Check API health"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def analyze_file(self, file_path: str):
        """Analyze STEP file - full analysis"""
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'application/step')}
            response = requests.post(f"{self.base_url}/analyze", files=files)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")
    
    def analyze_geometry(self, file_path: str):
        """Analyze only geometry"""
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'application/step')}
            response = requests.post(f"{self.base_url}/analyze/geometry", files=files)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")
    
    def analyze_topology(self, file_path: str):
        """Analyze only topology"""
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'application/step')}
            response = requests.post(f"{self.base_url}/analyze/topology", files=files)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")
    
    def validate_file(self, file_path: str):
        """Validate STEP file"""
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'application/step')}
            response = requests.post(f"{self.base_url}/validate", files=files)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")


def main():
    """Main test function"""
    
    # Initialize client
    client = STEPAPIClient()
    
    # Check if API is running
    print("🔍 Checking API health...")
    try:
        health = client.health_check()
        print(f"✅ API Status: {health['status']}")
        print(f"   OCCT Available: {health['occt_available']}")
        print()
    except Exception as e:
        print(f"❌ API is not running: {e}")
        print("   Start the API with: docker-compose up")
        return
    
    # Check for STEP file argument
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <path_to_step_file>")
        print("\nExample:")
        print("  python test_api.py sample.step")
        return
    
    step_file = sys.argv[1]
    
    if not Path(step_file).exists():
        print(f"❌ File not found: {step_file}")
        return
    
    print(f"📁 Analyzing file: {step_file}")
    print()
    
    # Test full analysis
    print("=" * 60)
    print("FULL ANALYSIS")
    print("=" * 60)
    try:
        result = client.analyze_file(step_file)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("GEOMETRY ONLY")
    print("=" * 60)
    try:
        result = client.analyze_geometry(step_file)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("TOPOLOGY ONLY")
    print("=" * 60)
    try:
        result = client.analyze_topology(step_file)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("VALIDATION")
    print("=" * 60)
    try:
        result = client.validate_file(step_file)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
