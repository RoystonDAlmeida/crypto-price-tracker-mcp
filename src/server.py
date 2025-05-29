"""
Crypto Price Tracker MCP Server
Main entry point for the MCP server implementation
"""

from mcp.server.fastmcp import FastMCP, Context # Import Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

import os
from datetime import datetime, timezone
import asyncio # Added for asyncio.to_thread
from typing import Dict, List, Optional

# Import modules for different components
from api_client import CryptoApiClient
from sheets_client import GoogleSheetsClient
from watchlist import WatchlistManager

# AppContext class that binds application components
@dataclass
class AppContext:
    """Application context for lifespan management"""

    api_client: CryptoApiClient
    sheets_client: Optional[GoogleSheetsClient]
    watchlist_manager: WatchlistManager

# app_lifespan context manager that initializes these components(services) and cleans them up
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""

    # Initialize API client
    api_client = CryptoApiClient()
    
    # Initialize Google Sheets client
    sheets_client = None
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "google_credentials.json")
    if os.path.exists(credentials_path):
        try:
            client_instance = GoogleSheetsClient(credentials_file=credentials_path)
            if client_instance.service:
                # Check if the service was initialised successfully
                sheets_client = client_instance
                print(f"Google Sheets client initialized successfully using {credentials_path}.")
            else:
                # GoogleSheetsClient._initialize_service already prints an error message
               print(f"Failed to initialize Google Sheets service using {credentials_path}. The service attribute was not set. Check logs from GoogleSheetsClient.")
        except Exception as e:
            print(f"Exception occurred during GoogleSheetsClient instantiation or service initialization with {credentials_path}: {e}")
    else:
        print(f"Google Sheets credentials file not found at '{credentials_path}'. Sheets client will not be available.")
    
    # Initialize watchlist manager
    watchlist_manager = WatchlistManager()
    
    # Yield the context with initialized components
    try:
        yield AppContext(
            api_client=api_client,
            sheets_client=sheets_client,
            watchlist_manager=watchlist_manager
        )
    finally:
        # Cleanup resources
        if sheets_client:
            await sheets_client.close()

# Create an MCP server instance
mcp = FastMCP("Crypto Price Tracker", lifespan=app_lifespan)

# # === Tools ===

@mcp.tool(
    name = "get_watchlist",
    description = "Get the current watchlist of tracked cryptocurrencies",
    annotations = {
        "title": "Get Watchlist",
        "readOnlyHint": "True", # Fetched data is read only
        "destuctiveHint": "False",
        "idemptotentHint": "True",
        "openWorldHint": "False"
    }
)
async def get_watchlist(ctx: Context):
    """
    Get the current watchlist of tracked cryptocurrencies

    Args:
        ctx: The MCP Context object.

    Returns:
        A string containing the current watchlist of tracked cryptocurrencies.
    """

    try:
        # Correctly access the AppContext instance from the injected ctx
        app_context = ctx.request_context.lifespan_context
        
        # Type check for robustness, though FastMCP should provide the correct context
        if not isinstance(app_context, AppContext):
            return "Error: Application context is not properly configured."
        
        watchlist_manager = app_context.watchlist_manager
        watchlist_data = watchlist_manager.get_watchlist()

        if not watchlist_data:
            return "Your watchlist is empty."

        output_lines = ["Current Watchlist:"]
        for coin, date_added_str in watchlist_data.items():
            # Parse the stored date string
            dt_object = datetime.strptime(date_added_str, '%Y-%m-%d %H:%M:%S')

            # Format it to dd-mm-yyyy
            formatted_date = dt_object.strftime('%d-%m-%Y')
            output_lines.append(f"- {coin} (Added on: {formatted_date})")
        return "\n".join(output_lines)
    
    except Exception as e:
        return f"Error fetching watchlist: {str(e)}"

@mcp.tool(
    name="add_to_watchlist",
    description="Add a cryptocurrency to the user's watchlist",
    annotations={
        "title": "Add Cryptocurrency to Watchlist",
        "readOnlyHint": False,
        "destructiveHint": False,  # Modifies data but is not destructive
        "idempotentHint": True,    # Adding the same coin twice has no additional effect
        "openWorldHint": False     # Operating on internal watchlist, not external systems
    }
)
def add_to_watchlist(id: str, ctx: Context) -> str: # Add ctx: Context parameter
    """Add a cryptocurrency to the user's watchlist for price tracking.
    
    This tool adds the specified cryptocurrency symbol to the user's watchlist
    for ongoing price monitoring. If the symbol is already in the watchlist,
    no action is taken.
    
    Args:
        symbol: The id of the cryptocurrency(Eg: "bitcoin", "ethereum", "osmosis-allbtc")
        ctx: The MCP Context object, automatically injected by FastMCP.
    
    Returns:
        A confirmation message indicating the id was added or was already present.
    
    Examples:
        > add_to_watchlist(id="bitcoin")
        "Added bitcoin to your watchlist."
        
        > add_to_watchlist(symbol="ethereum")  # When ethereum is already in watchlist
        "ethereum is already in your watchlist."
    """
    
    # Input validation
    if not id:
        return "Error: id cannot be empty."
    
    if not isinstance(id, str):
        return "Error: id must be a string."
    
    # Standardize the input("Bitcoin" -> "bitcoin")
    id = id.strip().lower()
    
    try:
        # Correctly access the AppContext instance from the injected ctx
        app_context = ctx.request_context.lifespan_context
        
        # Type check for robustness, though FastMCP should provide the correct context
        if not isinstance(app_context, AppContext):
            # Log this issue if you have a logger
            # print("Error: Application context is not an instance of AppContext.")
            return "Error: Application context is not properly configured."

        watchlist_manager = app_context.watchlist_manager
        
        # Check if already in watchlist
        if id in watchlist_manager.get_watchlist():
            return f"{id} is already in your watchlist."
        
        watchlist_manager.add_coin(id)
        return f"Added {id} to your watchlist."
    except AttributeError as e:
        return f"Error accessing application component: {str(e)}. Ensure AppContext and lifespan are set up correctly."
    except Exception as e:
        # General error handling
        return f"Error adding {id} to watchlist: {str(e)}"

@mcp.tool(
    name="remove_from_watchlist",
    description="Remove a cryptocurrency from the user's watchlist",
    annotations={
        "title": "Remove Crypto from Watchlist",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False 
    }
)
def remove_from_watchlist(id: str, ctx: Context) -> str:
    """Remove a cryptocurrency from the user's watchlist.
    
    This tool removes the specified cryptocurrency symbol from the user's watchlist.
    If the symbol is not in the watchlist, no action is taken.
    
    Args:
        id: The id of the cryptocurrency(Eg: "bitcoin", "ethereum", "osmosis-allbtc"))
        ctx: The MCP Context object, automatically injected by FastMCP.
    
    Returns:
        A confirmation message indicating the symbol was removed or was not present.
    
    Examples:
        > remove_from_watchlist(symbol="bitcoin")
        "Removed bitcoin from your watchlist."
        
        > remove_from_watchlist(symbol="xrp")  # When XRP is not in watchlist
        "xrp is not in your watchlist."
    """
    
    # Input validation
    if not id:
        return "Error: id cannot be empty."
    
    if not isinstance(id, str):
        return "Error: id must be a string."
    
    # Standardize the input
    id = id.strip().lower()
    
    try:
        # Correctly access the AppContext instance from the injected ctx
        app_context = ctx.request_context.lifespan_context
        
        # Type check for robustness, though FastMCP should provide the correct context
        if not isinstance(app_context, AppContext):
            return "Error: Application context is not properly configured."

        watchlist_manager = app_context.watchlist_manager
        
        # Check if in watchlist
        if id not in watchlist_manager.get_watchlist():
            return f"{id} is not in your watchlist."
        
        # Remove from watchlist
        watchlist_manager.remove_coin(id)
        return f"Removed {id} from your watchlist."
    except AttributeError as e:
        return f"Error accessing application component: {str(e)}. Ensure AppContext and lifespan are set up correctly."
    except Exception as e:
        # General error handling
        return f"Error removing {id} from watchlist: {str(e)}"

@mcp.tool(
        name="fetch_prices",
        description="Fetch the latest prices for all coins in the watchlist",
        annotations = {
            "title": "Fetch Prices",
            "readOnlyHint": "False",
            "destuctiveHint": "False",
            "idemptotentHint": "True",
            "openWorldHint": "True" # Interacting with CoinGecko API service
        }
)
async def fetch_all_prices(ctx: Context) -> str:
    """ Fetch the latest prices for all coins in the watchlist

        This tool fetches the current prices for all cryptos in the watchlist.
        If the watchlist is empty, the tool returns a message indicating that the watchlist is empty.

        Args:
            ctx: The MCP Context object, automatically injected by FastMCP.

        Returns:
            A string containing the current prices for all cryptos in the watchlist.

        Examples:
            > fetch_all_prices()
            "Current prices:\nbitcoin: $49,000.00 (0.00%)\nethereum: $2,500.00 (0.00%)"
    """

    try:
        # Correctly access the AppContext instance from the injected ctx
        app_context = ctx.request_context.lifespan_context
        
        # Type check for robustness, though FastMCP should provide the correct context
        if not isinstance(app_context, AppContext):
            return "Error: Application context is not properly configured."
        
        watchlist_manager = app_context.watchlist_manager
        watchlist = watchlist_manager.get_watchlist()

        api_client = app_context.api_client
    
        if not watchlist:
            return "Your watchlist is empty. Add coins using the add_to_watchlist tool."
    
        results = []
        for id in watchlist:
            price_data = await api_client.get_current_price(id)
            if price_data:
                results.append(f"{id}: ${price_data['price']} ({price_data['change_24h']}%)")
            else:
                results.append(f"{id}: Failed to fetch price")
        
        return "Current prices:\n" + "\n".join(results)
    
    except Exception as e:
        return f"Error fetching prices: {str(e)}"

@mcp.tool(
        name="export_to_sheets",
        description="Export all tracked price data to Google Sheets",
        annotations = { 
            "title": "Export to Google Sheets",
            "readOnlyHint": "False",
            "destuctiveHint": "True",
            "idemptotentHint": "True",
            "openWorldHint": "True" # Interacting with Google Sheets
        }
)
async def export_to_sheets(sheet_name: str, user_email: str, ctx: Context) -> str:
    """ Export all tracked price data to Google Sheets


        Args:
            sheet_name: The name of the sheet (and spreadsheet) to create/use.
            user_email: The Google email address to share the spreadsheet with.
            ctx: The MCP Context object.
    """

    try:
        app_context = ctx.request_context.lifespan_context
        
        if not isinstance(app_context, AppContext):
            return "Error: Application context is not properly configured."

        sheets_client = app_context.sheets_client
        if not sheets_client:
            return "Google Sheets integration is not configured. Please set up credentials."

        watchlist_manager = app_context.watchlist_manager
        watchlist = watchlist_manager.get_watchlist()
        
        if not watchlist:
            return "Your watchlist is empty. Add coins using the add_to_watchlist tool."
        
        api_client = app_context.api_client
        
        # Prepare data for export
        export_data = []
        for coin_id, date_added in watchlist.items():
            price_data = await api_client.get_current_price(coin_id)
            if price_data:
                formatted_last_updated = None
                last_updated_utc_str = price_data.get('last_updated')

                if last_updated_utc_str:
                    try:
                        # Parse the ISO 8601 UTC timestamp string.
                        # The .replace('Z', '+00:00') ensures it's parsed as UTC.
                        utc_dt = datetime.fromisoformat(last_updated_utc_str.replace('Z', '+00:00'))
                        
                        # Convert to local timezone
                        local_dt = utc_dt.astimezone()
                        
                        # Format to a string similar to other date fields
                        formatted_last_updated = local_dt.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError as ve:
                        print(f"Warning: Could not parse 'last_updated' timestamp '{last_updated_utc_str}' for {coin_id}: {ve}. Using original value.")
                        formatted_last_updated = last_updated_utc_str # Fallback to original string
                    except Exception as e_ts:
                        print(f"Warning: An unexpected error occurred during timestamp conversion for {coin_id}: {e_ts}. Using original value.")
                        formatted_last_updated = last_updated_utc_str # Fallback to original string

                export_data.append({
                    'Symbol': price_data.get('symbol'),
                    'Id': coin_id,
                    'Name': price_data.get('name'),
                    'Price': price_data.get('price'),
                    'Change_24h': price_data.get('change_24h'),
                    'Last_Updated': formatted_last_updated,
                    'Added_On': date_added 
                })
        
        if sheets_client.export_data(sheet_name, export_data, user_email_to_share=user_email):
            spreadsheet_url = sheets_client.get_spreadsheet_url()
            if spreadsheet_url:
                return f"Successfully exported price data to '{sheet_name}' sheet.\nURL: {spreadsheet_url}"
            else:
                return f"Successfully exported price data to '{sheet_name}' sheet."
        else:
            return "Failed to export data to Google Sheets."
            
    except Exception as e:
        return f"Error exporting to Google Sheets: {str(e)}"

# === Analyze Sheet Performance ===
@mcp.tool(
    name="get_sheet_performance_leaders",
    description="Identifies cryptocurrencies with the highest gain and highest loss from a Google Sheet based on 'Change_24h'.",
    annotations={
        "title": "Get Performance Leaders from Sheet",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True # Interacting with Google Sheets
    }
)
async def get_sheet_performance_leaders(sheet_name: str, ctx: Context) -> str:
    """
    Identifies the cryptocurrencies from the specified Google Sheet
    that had the highest gain and highest loss based on the 'Change_24h' column.
    Assumes the sheet was created by the 'export_to_sheets' tool.

    Args:
        sheet_name: The name of the Google Sheet to analyze.
        ctx: The MCP Context object.

    Returns:
        A string summarizing the best and worst performers, or an error message.
    """
    try:
        app_context = ctx.request_context.lifespan_context
        if not isinstance(app_context, AppContext):
            return "Error: Application context is not properly configured."

        sheets_client = app_context.sheets_client
        if not sheets_client or not sheets_client.service:
            return "Google Sheets integration is not configured or not initialized. Please set up credentials."

        # Find the spreadsheet ID using the new method (run sync method in thread)
        spreadsheet_id = await asyncio.to_thread(sheets_client.find_spreadsheet_by_title, sheet_name)
        if not spreadsheet_id:
            return f"Error: Could not find Google Sheet named '{sheet_name}'. Ensure it has been created/shared correctly."

        # Read data from the sheet (run sync method in thread)
        # Assumes data is in 'Sheet1' and includes headers.
        raw_data = await asyncio.to_thread(sheets_client.read_sheet_data, spreadsheet_id, 'Sheet1!A:Z')

        if not raw_data or len(raw_data) < 2: # Need header + at least one data row
            return f"No data or insufficient data found in sheet '{sheet_name}'. The sheet might be empty or improperly formatted."

        header = raw_data[0]
        data_rows = raw_data[1:]

        try:
            # Determine column for coin identification (Id, Symbol, or Name)
            id_col_name = next((col for col in ['Id', 'Symbol', 'Name'] if col in header), None)
            if not id_col_name:
                 return "Error: Could not find a suitable identifier column (Id, Symbol, or Name) in the sheet header."
            id_col_index = header.index(id_col_name)
            change_col_index = header.index('Change_24h')
        except ValueError:
            return "Error: Sheet is missing 'Change_24h' column or a required identifier column in the header."

        highest_gain = -float('inf')
        biggest_gainer_info = "N/A"
        lowest_loss = float('inf') # Using 'lowest_loss' to find the most negative value
        biggest_loser_info = "N/A"

        for row_num, row in enumerate(data_rows, start=2): # start=2 for 1-based indexing + header
            if len(row) <= max(id_col_index, change_col_index) or not row[change_col_index]:
                # Skip malformed rows or rows where Change_24h is empty
                continue
            
            try:
                coin_identifier = row[id_col_index]
                change_str = str(row[change_col_index]).strip().rstrip('%') # Strip whitespace before rstrip
                change_val = float(change_str)

                if change_val > highest_gain:
                    highest_gain = change_val
                    biggest_gainer_info = f"{coin_identifier} ({highest_gain:.2f}%)"
                
                if change_val < lowest_loss:
                    lowest_loss = change_val
                    biggest_loser_info = f"{coin_identifier} ({lowest_loss:.2f}%)"
            except (ValueError, TypeError):
                print(f"Warning: Skipping row {row_num} in sheet '{sheet_name}' due to data conversion error for 'Change_24h': {row[change_col_index]}")
                continue 

        if highest_gain == -float('inf') and lowest_loss == float('inf'):
            return f"Could not determine performance leaders from '{sheet_name}'. No valid data found or all 'Change_24h' values were non-numeric."

        return f"Performance Leaders from '{sheet_name}':\n- Highest Gain: {biggest_gainer_info}\n- Biggest Loss: {biggest_loser_info}"

    except Exception as e:
        return f"Error analyzing sheet performance for '{sheet_name}': {str(e)}"

# === Prompts ===
@mcp.prompt(
    name="get_watchlist_prompt",
    description="Generates a prompt to retrieve the user's watchlist."
)
def get_watchlist_prompt() -> str:
    """
    Generates a prompt to retrieve the user's watchlist.
    
    Returns:
        A formatted prompt string requesting to retrieve the user's watchlist.
    
    Example:
        get_watchlist_prompt() -> 'Please fetch the watchlist
    """

    return "Please fetch the watchlist."

@mcp.prompt(
    name="add_coin_prompt",
    description="Generates a prompt to add a cryptocurrency to the user's watchlist and retrieve its current price."
)
def add_coin_prompt(coin_symbol: str) -> str:
    """
    Generates a prompt to add a cryptocurrency to the user's watchlist and retrieve its current price.
    
    Args:
        coin_symbol: The trading symbol of the cryptocurrency (e.g., 'BTC', 'ETH', 'SOL').
                     Should be provided in uppercase without special characters.
    
    Returns:
        A formatted prompt string requesting to add the specified coin to the watchlist
        and display its current price.
    
    Raises:
        ValueError: If coin_symbol is empty or contains invalid characters.
    
    Example:
        add_coin_prompt('BTC') -> 'Please add BTC to my watchlist and show me its current price.'
    """

    # Validate required argument
    if not coin_symbol:
        raise ValueError("Coin symbol cannot be empty")

    # Validate argument format
    if not isinstance(coin_symbol, str) or not coin_symbol.strip():
        raise ValueError("Coin symbol must be a non-empty string")
    
    # Standardize input format
    coin_symbol = coin_symbol.strip().upper()

    # Generate and return the formatted prompt
    return f"Please add {coin_symbol} to my watchlist and show me its current price."


@mcp.prompt(
    name = "remove_coin_prompt",
    description="Generates a prompt to remove a cryptocurrency from the user's watchlist."
)
def remove_coin_prompt(coin_symbol: str) -> str:
    """
    Generates a prompt to remove a cryptocurrency from the user's watchlist.
    
    Args:
        coin_symbol: The trading symbol of the cryptocurrency (e.g., 'BTC', 'ETH', 'SOL').
                   Should be provided in uppercase without special characters.
    
    Returns:
        A formatted prompt string requesting to remove the specified coin from the watchlist.
    
    Raises:
        ValueError: If coin_symbol is empty or contains invalid characters.
    
    Example:
        remove_coin_prompt('BTC') -> 'Please remove BTC from my watchlist.'
    """
    
    # Validate required argument
    if not coin_symbol:
        raise ValueError("Coin symbol cannot be empty")
    
    # Validate argument format
    if not isinstance(coin_symbol, str) or not coin_symbol.strip():
        raise ValueError("Coin symbol must be a non-empty string")
        
    # Standardize input format
    coin_symbol = coin_symbol.strip().lower()
    
    # Generate and return the formatted prompt
    return f"Please remove {coin_symbol} from my watchlist."

@mcp.prompt(
    name = "get_prices_prompt",
    description="Generates a prompt to fetch the latest prices for all cryptocurrencies in the user's watchlist."
)
def get_prices_prompt() -> str:
    """
    Generates a prompt to fetch the latest prices for all cryptocurrencies in the user's watchlist.
    
    Returns:
        A formatted prompt string requesting to fetch all cryptocurrency prices from the watchlist.
    
    Example:
        get_prices_prompt() -> 'Please fetch the latest prices for all cryptocurrencies in my watchlist.'
    """

    return "Please fetch the latest prices for all cryptocurrencies in my watchlist."

@mcp.prompt(
    name = "export_prompt",
    description="Generates a prompt to export data to a Google Sheet and share it with a specific user."
)
def export_prompt(sheet_name: str, user_email: str) -> str:
    """
    Prompt template for exporting to Google Sheets and sharing it.
    Args:
        sheet_name: The desired name for the Google Sheet.
        user_email: The email address to share the sheet with.
    """

    return f"Please export all tracked price data to my Google Sheet '{sheet_name}' and share it with {user_email}."

@mcp.prompt(
    name="get_sheet_performance_leaders_prompt",
    description="Generates a prompt to identify the best and worst performing cryptocurrencies from a specified Google Sheet."
)
def get_sheet_performance_leaders_prompt(sheet_name: str) -> str:
    """
    Generates a prompt to request an analysis of cryptocurrency performance
    leaders from a Google Sheet.

    Args:
        sheet_name: The name of the Google Sheet to analyze.
                    It should be a non-empty string.

    Returns:
        A formatted prompt string.

    Raises:
        ValueError: If sheet_name is empty or not a string.
    """
    if not sheet_name or not isinstance(sheet_name, str) or not sheet_name.strip():
        raise ValueError("Sheet name must be a non-empty string.")
    
    return f"From the Google Sheet named '{sheet_name}', can you tell me which crypto had the highest gain and which one had the biggest loss recently?"

if __name__ == "__main__":

    # Run the MCP server
    mcp.run(transport="stdio")