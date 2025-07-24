import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import httpx

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in the .env file.")

genai.configure(api_key=api_key)

# --- Gemini Model Configuration ---

# Initialize the generative model
# We use gemini-1.5-flash for its speed and function-calling capabilities
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction="You are a helpful and friendly assistant for a conversational commerce application. Your goal is to help users find products and hotels using the SearchLift360 platform. You have access to the following tools: get categories (to browse product categories), get all products, search products by keywords, and search hotels by location. When you receive results from a tool, present them clearly and concisely to the user with relevant details like prices, descriptions, and availability. Do not make up information. If a tool call fails, inform the user gracefully and suggest alternatives."
)

async def generate_response_with_gemini(user_prompt: str, tools: list, mcp_instance=None):
    """
    Manages the conversation with the Gemini model, including function calling.

    Args:
        user_prompt (str): The user's input.
        tools (list): A list of tool definitions (from FastMCP).
        mcp_instance: The FastMCP instance to call tools on.

    Returns:
        str: The model's final text response.
    """
    try:
        # Start a chat session with the model
        chat = model.start_chat(enable_automatic_function_calling=False) # We will handle it manually for clarity

        # Send the user's prompt to the model, along with the available tools
        response = chat.send_message(user_prompt, tools=tools)
        response_message = response.candidates[0].content

        # --- Loop to handle potential multi-turn tool calls ---
        while (
            hasattr(response_message, "parts")
            and response_message.parts
            and hasattr(response_message.parts[0], "function_call")
            and response_message.parts[0].function_call
        ):
            function_call = response_message.parts[0].function_call
            
            # Extract the function name and arguments
            tool_name = function_call.name
            tool_args = {key: value for key, value in function_call.args.items()}
            
            print(f"Gemini requested to call tool: {tool_name} with args: {tool_args}")

            # --- Execute the tool ---
            try:
                # Call the tool using FastMCP
                if mcp_instance:
                    tool_response_data = await execute_mcp_tool(mcp_instance, tool_name, tool_args)
                else:
                    # Fallback to direct HTTP calls
                    tool_response_data = await execute_local_tool(tool_name, tool_args)
                
                # --- FIX: Wrap list responses in a dictionary ---
                if isinstance(tool_response_data, list):
                    tool_response_data = {"results": tool_response_data}
                # --- END FIX ---

                # Format the response for Gemini
                tool_response = {
                    "name": tool_name,
                    "response": tool_response_data  # Use response instead of content, and pass raw data
                }
                
                print(f"Tool {tool_name} executed successfully. Response: {tool_response_data}")

                # Send the tool's response back to the model
                response = chat.send_message(
                    [genai.protos.Part(function_response=genai.protos.FunctionResponse(**tool_response))],
                )
                response_message = response.candidates[0].content

            except Exception as e:
                print(f"Error executing tool {tool_name}: {e}")
                # If tool execution fails, send an error message back to the model
                error_response = {
                    "name": tool_name,
                    "response": {"error": f"Failed to execute tool: {str(e)}"}  # Use response instead of content
                }
                response = chat.send_message(
                    [genai.protos.Part(function_response=genai.protos.FunctionResponse(**error_response))],
                )
                response_message = response.candidates[0].content

        # --- Return the final text response from the model ---
        if (
            hasattr(response.candidates[0].content, "parts")
            and response.candidates[0].content.parts
            and hasattr(response.candidates[0].content.parts[0], "text")
            and response.candidates[0].content.parts[0].text
        ):
            return response.candidates[0].content.parts[0].text
        else:
            # This can happen if the model only returns a tool call but no final text
            return "I have processed your request. Is there anything else I can help with?"

    except Exception as e:
        print(f"An unexpected error occurred in generate_response_with_gemini: {e}")
        # It's good practice to have a fallback response
        return "I'm sorry, but I encountered an error while trying to process your request. Please try again later."


async def execute_mcp_tool(mcp_instance, tool_name: str, tool_args: dict):
    """
    Execute a tool using the FastMCP instance.
    
    Args:
        mcp_instance: The FastMCP instance
        tool_name (str): Name of the tool to call
        tool_args (dict): Arguments to pass to the tool
    
    Returns:
        dict: Response from the tool
    """
    try:
        # Get the tool by name
        tool = await mcp_instance.get_tool(tool_name)
        
        # Call the tool function directly
        if hasattr(tool, 'fn') and callable(tool.fn):
            if tool_args:
                result = await tool.fn(**tool_args)
            else:
                result = await tool.fn()
            return result
        else:
            raise ValueError(f"Tool {tool_name} is not callable")
            
    except Exception as e:
        print(f"Error executing MCP tool {tool_name}: {e}")
        # Fallback to local execution
        return await execute_local_tool(tool_name, tool_args)


async def execute_local_tool(tool_name: str, tool_args: dict):
    """
    Execute a tool by making HTTP requests to the local FastAPI server.
    
    Args:
        tool_name (str): Name of the tool/endpoint to call
        tool_args (dict): Arguments to pass to the tool
    
    Returns:
        dict: Response from the tool
    """
    base_url = "http://localhost:8001"
    
    async with httpx.AsyncClient() as client:
        if tool_name == "get_categories_tool":
            response = await client.get(f"{base_url}/categories")
        elif tool_name == "get_products_tool":
            response = await client.get(f"{base_url}/products")
        elif tool_name == "search_products_tool":
            search_term = tool_args.get("searchTerm", "")
            response = await client.get(f"{base_url}/products/search", params={"searchTerm": search_term})
        elif tool_name == "search_hotels_tool":
            response = await client.get(f"{base_url}/hotels/search", params=tool_args)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        response.raise_for_status()
        return response.json()
