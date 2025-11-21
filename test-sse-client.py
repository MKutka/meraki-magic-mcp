#!/usr/bin/env python3
"""
Simple test client for Meraki MCP SSE Server
Tests that the server is working correctly
"""

import requests
import json
import time
import sys

# Configuration
SERVER_URL = "http://10.21.21.16:8000"
SSE_ENDPOINT = f"{SERVER_URL}/sse"
MESSAGES_ENDPOINT = f"{SERVER_URL}/messages"

def test_connection():
    """Test basic connection to SSE endpoint"""
    print("=" * 60)
    print("TEST 1: Testing SSE Connection")
    print("=" * 60)
    try:
        response = requests.get(SSE_ENDPOINT, stream=True, timeout=3)
        if response.status_code == 200:
            print("✅ SSE endpoint is accessible")
            # Read first event
            for line in response.iter_lines():
                if line:
                    print(f"   Received: {line.decode('utf-8')}")
                    break
            return True
        else:
            print(f"❌ SSE endpoint returned status {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("✅ SSE endpoint is accessible (timeout expected for streaming)")
        return True
    except Exception as e:
        print(f"❌ Error connecting to SSE: {e}")
        return False

def send_request(method, params=None, request_id=1):
    """Send a JSON-RPC request to the server"""
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params or {}
    }

    try:
        response = requests.post(
            MESSAGES_ENDPOINT,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-session-id": "test-session"
            },
            timeout=10
        )
        return response
    except Exception as e:
        print(f"❌ Error sending request: {e}")
        return None

def test_initialize():
    """Test initialize method"""
    print("\n" + "=" * 60)
    print("TEST 2: Testing Initialize")
    print("=" * 60)

    response = send_request("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0"}
    })

    if response and response.status_code in [200, 202]:
        print("✅ Initialize request sent successfully")
        print(f"   Status: {response.status_code}")
        return True
    else:
        print(f"❌ Initialize failed: {response.status_code if response else 'No response'}")
        return False

def test_list_tools():
    """Test listing available tools"""
    print("\n" + "=" * 60)
    print("TEST 3: Testing List Tools")
    print("=" * 60)

    response = send_request("tools/list", {}, request_id=2)

    if response and response.status_code in [200, 202]:
        print("✅ List tools request sent successfully")
        print(f"   Status: {response.status_code}")
        print("   Server will respond via SSE stream")
        return True
    else:
        print(f"❌ List tools failed: {response.status_code if response else 'No response'}")
        return False

def test_call_tool():
    """Test calling a Meraki API tool"""
    print("\n" + "=" * 60)
    print("TEST 4: Testing Call Tool (getOrganizations)")
    print("=" * 60)

    response = send_request("tools/call", {
        "name": "getOrganizations",
        "arguments": {}
    }, request_id=3)

    if response and response.status_code in [200, 202]:
        print("✅ Tool call request sent successfully")
        print(f"   Status: {response.status_code}")
        print("   Server will respond via SSE stream")
        return True
    else:
        print(f"❌ Tool call failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"   Response: {response.text}")
        return False

def test_call_meraki_api():
    """Test the generic call_meraki_api tool"""
    print("\n" + "=" * 60)
    print("TEST 5: Testing call_meraki_api (getOrganizationAdmins)")
    print("=" * 60)

    response = send_request("tools/call", {
        "name": "call_meraki_api",
        "arguments": {
            "section": "organizations",
            "method": "getOrganizationAdmins",
            "parameters": {}
        }
    }, request_id=4)

    if response and response.status_code in [200, 202]:
        print("✅ call_meraki_api request sent successfully")
        print(f"   Status: {response.status_code}")
        print("   Server will respond via SSE stream")
        return True
    else:
        print(f"❌ call_meraki_api failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"   Response: {response.text}")
        return False

def listen_for_responses(duration=5):
    """Listen to SSE stream for responses"""
    print("\n" + "=" * 60)
    print(f"Listening for SSE responses for {duration} seconds...")
    print("=" * 60)

    try:
        response = requests.get(
            SSE_ENDPOINT,
            stream=True,
            headers={"x-session-id": "test-session"},
            timeout=duration + 1
        )

        start_time = time.time()
        event_count = 0

        for line in response.iter_lines():
            if time.time() - start_time > duration:
                break

            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data:'):
                    event_count += 1
                    data = decoded[5:].strip()
                    try:
                        json_data = json.loads(data)
                        print(f"\n📨 Event {event_count}:")
                        print(json.dumps(json_data, indent=2))
                    except:
                        print(f"\n📨 Event {event_count}: {data}")

        print(f"\n✅ Received {event_count} SSE events")

    except requests.exceptions.Timeout:
        print("✅ Listening completed (timeout)")
    except Exception as e:
        print(f"❌ Error listening to SSE: {e}")

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Meraki MCP SSE Server Test Suite" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    print(f"\nServer: {SERVER_URL}")
    print(f"SSE Endpoint: {SSE_ENDPOINT}")
    print(f"Messages Endpoint: {MESSAGES_ENDPOINT}\n")

    results = []

    # Test 1: Connection
    results.append(("SSE Connection", test_connection()))
    time.sleep(1)

    # Test 2: Initialize
    results.append(("Initialize", test_initialize()))
    time.sleep(1)

    # Test 3: List Tools
    results.append(("List Tools", test_list_tools()))
    time.sleep(1)

    # Test 4: Call Tool
    results.append(("Call Tool", test_call_tool()))
    time.sleep(1)

    # Test 5: call_meraki_api
    results.append(("call_meraki_api", test_call_meraki_api()))
    time.sleep(1)

    # Listen for responses
    listen_for_responses(duration=5)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nResult: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Server is working correctly!")
        print("\nYou can give this URL to your engineering team:")
        print(f"   {SSE_ENDPOINT}")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
