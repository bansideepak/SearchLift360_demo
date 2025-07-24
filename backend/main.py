import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Any

from chat_handler import generate_response_with_gemini
from mcp_server import mcp

# --- Configuration for External API ---
ECOMMERCE_API_BASE_URL = "https://app.searchlift360.com/ecommerce/api/public"
HOTEL_API_BASE_URL = "https://app.searchlift360.com/hotel/api/public"


# --- Pydantic Models for SearchLift360 API Responses ---

class Category(BaseModel):
    id: int
    name: str
    description: str
    parent_category_id: Optional[int] = None
    created_at: str
    updated_at: str

class Product(BaseModel):
    id: int
    name: str
    description: str
    price: str
    stock_quantity: int
    image_url: str
    category_id: int
    category_name: str
    created_at: str
    updated_at: str

class Hotel(BaseModel):
    id: int
    name: str
    city: str
    state: str
    country: str
    postal_code: str
    description: str
    star_rating: int
    image_url: str

class HotelSearchResponse(BaseModel):
    message: str
    count: int
    hotels: List[Hotel]


# --- FastAPI Application Setup ---

app = FastAPI(
    title="Conversational Commerce API (SearchLift360 Edition)",
    description="Backend APIs integrated with the SearchLift360 platform. Endpoints are exposed as tools for Gemini.",
    version="2.0.0",
)

# --- Tool-Exposed API Endpoints ---
# These functions now act as clients for the SearchLift360 API.

@app.get("/categories", tags=["E-commerce"])
async def get_categories():
    """
    Fetch all product categories available in the ecommerce system via the SearchLift360 API.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{ECOMMERCE_API_BASE_URL}/categories")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Error from SearchLift360 API: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Could not connect to the SearchLift360 categories API: {e}")


@app.get("/products", tags=["E-commerce"])
async def get_products():
    """
    Fetch all products along with their associated category via the SearchLift360 API.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{ECOMMERCE_API_BASE_URL}/products")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Error from SearchLift360 API: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Could not connect to the SearchLift360 products API: {e}")


@app.get("/products/search", tags=["E-commerce"])
async def search_products(searchTerm: str):
    """
    Search for products using a search term via the SearchLift360 ecommerce API.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{ECOMMERCE_API_BASE_URL}/products/search",
                params={"searchTerm": searchTerm}
            )
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            return response.json()
        except httpx.HTTPStatusError as e:
            # Forward the error from the downstream API
            raise HTTPException(status_code=e.response.status_code, detail=f"Error from SearchLift360 API: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Could not connect to the SearchLift360 product API: {e}")


@app.get("/hotels/search", tags=["Hotels"])
async def search_hotels(
    location: str,
    checkInDate: Optional[str] = None,
    checkOutDate: Optional[str] = None,
    numGuests: Optional[int] = None,
    roomType: Optional[str] = None,
):
    """
    Search for hotels based on location and other optional criteria using the SearchLift360 hotel API.
    Dates should be in YYYY-MM-DD format.
    """
    params = {
        "location": location,
        "checkInDate": checkInDate,
        "checkOutDate": checkOutDate,
        "numGuests": numGuests,
        "roomType": roomType,
    }
    # Filter out None values so they aren't sent as query parameters
    cleaned_params = {k: v for k, v in params.items() if v is not None}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{HOTEL_API_BASE_URL}/search",
                params=cleaned_params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Error from SearchLift360 API: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Could not connect to the SearchLift360 hotel API: {e}")


# --- MCP Tool Definitions ---
# These are the actual functions that will be called by the Gemini model

@mcp.tool
async def get_categories_tool():
    """Fetch all product categories available in the ecommerce system"""
    return await get_categories()

@mcp.tool  
async def get_products_tool():
    """Fetch all products along with their associated category"""
    return await get_products()

@mcp.tool
async def search_products_tool(searchTerm: str):
    """Search for products using a search term"""
    return await search_products(searchTerm)

@mcp.tool
async def search_hotels_tool(
    location: str,
    checkInDate: Optional[str] = None,
    checkOutDate: Optional[str] = None,
    numGuests: Optional[int] = None,
    roomType: Optional[str] = None,
):
    """Search for hotels based on location and other criteria"""
    return await search_hotels(location, checkInDate, checkOutDate, numGuests, roomType)


# --- Conversational Chat Endpoint ---

class ChatRequest(BaseModel):
    prompt: str
    history: Optional[List[dict]] = []

@app.post("/chat", tags=["Conversational AI"])
async def chat_with_agent(request: ChatRequest):
    """
    Handles the conversational exchange with the Gemini model, using the SearchLift360 tools.
    """
    if not request.prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    try:
        # Manually define tools for Gemini (bypassing FastMCP for now)
        tools = [
            {
                "function_declarations": [
                    {
                        "name": "get_categories_tool",
                        "description": "Fetch all product categories available in the ecommerce system",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    },
                    {
                        "name": "get_products_tool", 
                        "description": "Fetch all products along with their associated category",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    },
                    {
                        "name": "search_products_tool",
                        "description": "Search for products using a search term",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "searchTerm": {
                                    "type": "string",
                                    "description": "The search term to look for products"
                                }
                            },
                            "required": ["searchTerm"]
                        }
                    },
                    {
                        "name": "search_hotels_tool",
                        "description": "Search for hotels based on location and other criteria",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {
                                    "type": "string", 
                                    "description": "Location to search for hotels"
                                },
                                "checkInDate": {
                                    "type": "string",
                                    "description": "Check-in date in YYYY-MM-DD format"
                                },
                                "checkOutDate": {
                                    "type": "string", 
                                    "description": "Check-out date in YYYY-MM-DD format"
                                },
                                "numGuests": {
                                    "type": "integer",
                                    "description": "Number of guests"
                                },
                                "roomType": {
                                    "type": "string",
                                    "description": "Type of room required"
                                }
                            },
                            "required": ["location"]
                        }
                    }
                ]
            }
        ]
        
        response_text = await generate_response_with_gemini(
            user_prompt=request.prompt,
            tools=tools,
            mcp_instance=None  # Using direct HTTP calls instead
        )
        return {"response": response_text}
    except Exception as e:
        print(f"Error during chat processing: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while processing your request: {e}")

# Mount the MCP server to expose the tool definitions at /mcp/tools
app.mount("/mcp", mcp)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
