#!/usr/bin/env python3
"""
Simple test script to verify the SearchLift360 API endpoints are working.
Run this after starting the FastAPI server to test the integration.
"""

import asyncio
import httpx

async def test_api_endpoints():
    """Test all the API endpoints"""
    base_url = "http://localhost:8001"
    
    async with httpx.AsyncClient() as client:
        print("Testing API endpoints...\n")
        
        # Test categories endpoint
        try:
            print("1. Testing /categories endpoint:")
            response = await client.get(f"{base_url}/categories")
            if response.status_code == 200:
                categories = response.json()
                print(f"   ✅ Success! Found {len(categories)} categories")
                if categories:
                    print(f"   Sample category: {categories[0]['name']}")
            else:
                print(f"   ❌ Failed with status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test products endpoint
        try:
            print("2. Testing /products endpoint:")
            response = await client.get(f"{base_url}/products")
            if response.status_code == 200:
                products = response.json()
                print(f"   ✅ Success! Found {len(products)} products")
                if products:
                    print(f"   Sample product: {products[0]['name']} - ${products[0]['price']}")
            else:
                print(f"   ❌ Failed with status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test product search endpoint
        try:
            print("3. Testing /products/search endpoint:")
            response = await client.get(f"{base_url}/products/search?searchTerm=shoes")
            if response.status_code == 200:
                products = response.json()
                print(f"   ✅ Success! Found {len(products)} products matching 'shoes'")
                if products:
                    print(f"   Sample result: {products[0]['name']} - ${products[0]['price']}")
            else:
                print(f"   ❌ Failed with status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test chat endpoint
        try:
            print("4. Testing /chat endpoint:")
            chat_data = {
                "prompt": "Show me some products in the accessories category",
                "history": []
            }
            response = await client.post(f"{base_url}/chat", json=chat_data)
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success! Chat response received")
                print(f"   Response preview: {result['response'][:100]}...")
            else:
                print(f"   ❌ Failed with status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("SearchLift360 API Integration Test")
    print("==================================")
    print("Make sure your FastAPI server is running on localhost:8001")
    print("Also ensure you have set the GEMINI_API_KEY in your .env file\n")
    
    asyncio.run(test_api_endpoints())
