"""
Test script to verify Aethel API integration
"""

import requests
import json

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{API_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✅ Health check passed")

def test_examples():
    """Test examples endpoint"""
    print("\n🔍 Testing examples endpoint...")
    response = requests.get(f"{API_URL}/api/examples")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["count"] == 3
    print(f"✅ Examples endpoint passed ({data['count']} examples)")

def test_verify():
    """Test verification endpoint"""
    print("\n🔍 Testing verification endpoint...")
    
    code = """intent transfer(sender: Account, receiver: Account, amount: Balance) {
    guard {
        sender_balance >= amount;
        amount > 0;
    }
    
    verify {
        sender_balance == old_sender_balance - amount;
        receiver_balance == old_receiver_balance + amount;
    }
}"""
    
    response = requests.post(
        f"{API_URL}/api/verify",
        json={"code": code},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    assert response.status_code == 200
    print("✅ Verification endpoint passed")

def main():
    print("🚀 Aethel API Integration Test\n")
    print("=" * 50)
    
    try:
        test_health()
        test_examples()
        test_verify()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed!")
        print("\n✅ Backend API is working correctly")
        print("✅ Frontend can now connect to http://localhost:8000")
        print("\n🌐 Open http://localhost:3000 to test Aethel Studio")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
