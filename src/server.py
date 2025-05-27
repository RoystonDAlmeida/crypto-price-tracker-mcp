"""
Crypto Price Tracker MCP Server
Main entry point for the MCP server implementation
"""

from mcp.server.fastmcp import FastMCP, Context # Import Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

import os
from datetime import datetime
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
    
    # Initialize Google Sheets client if credentials are available
    sheets_client = None
    if os.path.exists("credentials.json"):
        try:
            sheets_client = GoogleSheetsClient("credentials.json")
        except Exception as e:
            print(f"Failed to initialize Google Sheets client: {e}")
    
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

# # === Resources ===

# @mcp.resource("watchlist://all")
# async def get_watchlist():
#     """Get the current watchlist of tracked cryptocurrencies"""
#     # Access lifespan context directly from the MCP object
#     watchlist = mcp.lifespan_context.watchlist_manager.get_watchlist()
#     return "\n".join([f"{coin} - Added on {date}" for coin, date in watchlist.items()])


# @mcp.resource("price://{symbol}")
# async def get_current_price(symbol: str):
#     """Get the current price of a specific cryptocurrency"""
#     api_client = mcp.lifespan_context.api_client
#     price_data = await api_client.get_current_price(symbol)
    
#     if not price_data:
#         return f"Could not fetch price for {symbol}"
    
#     return (f"Current price for {symbol}: ${price_data['price']}\n"
#             f"24h Change: {price_data['change_24h']}%\n"
#             f"Last Updated: {price_data['last_updated']}")


# @mcp.resource("price://{symbol}/history/{timeframe}")
# async def get_price_history(symbol: str, timeframe: str):
#     """Get historical price data for a cryptocurrency"""
#     api_client = mcp.lifespan_context.api_client
#     history = await api_client.get_price_history(symbol, timeframe)
    
#     if not history:
#         return f"Could not fetch price history for {symbol} over {timeframe}"
    
#     # Format history data for display
#     result = [f"Price history for {symbol} over {timeframe}:"]
#     for entry in history:
#         result.append(f"{entry['date']}: ${entry['price']}")
    
#     return "\n".join(result)


# @mcp.resource("sheets://status")
# async def get_sheets_status():
#     """Get the status of Google Sheets integration"""
#     sheets_client = mcp.lifespan_context.sheets_client
    
#     if not sheets_client:
#         return "Google Sheets integration is not configured. Please set up credentials."
    
#     return (f"Google Sheets integration is active.\n"
#             f"Connected to: {sheets_client.get_active_spreadsheet()}")


# # === Tools ===

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


# @mcp.tool()
# async def export_to_sheets(sheet_name: str) -> str:
#     """Export all tracked price data to Google Sheets"""
#     sheets_client = mcp.lifespan_context.sheets_client
#     watchlist_manager = mcp.lifespan_context.watchlist_manager
#     api_client = mcp.lifespan_context.api_client
    
#     if not sheets_client:
#         return "Google Sheets integration is not configured. Please set up credentials."
    
#     watchlist = watchlist_manager.get_watchlist()
    
#     if not watchlist:
#         return "Your watchlist is empty. Add coins using the add_to_watchlist tool."
    
#     # Prepare data for export
#     export_data = []
#     for symbol in watchlist:
#         price_data = await api_client.get_current_price(symbol)
#         if price_data:
#             export_data.append({
#                 'Symbol': symbol,
#                 'Price': price_data['price'],
#                 'Change_24h': price_data['change_24h'],
#                 'Last_Updated': price_data['last_updated'],
#                 'Added_On': watchlist[symbol]
#             })
    
#     # Export to Google Sheets
#     try:
#         sheets_client.export_data(sheet_name, export_data)
#         return f"Successfully exported price data to '{sheet_name}' sheet."
#     except Exception as e:
#         return f"Failed to export data: {str(e)}"


# === Prompts ===

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
    coin_symbol = coin_symbol.strip().upper()
    
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

@mcp.prompt()
def price_history_prompt(coin_symbol: str, timeframe: str) -> str:
    """Prompt template for showing price history"""
    return f"Please show me the price history for {coin_symbol} over the past {timeframe}."


@mcp.prompt()
def export_prompt(sheet_name: str) -> str:
    """Prompt template for exporting to Google Sheets"""
    return f"Please export all tracked price data to my Google Sheet '{sheet_name}'."


if __name__ == "__main__":

    # Run the MCP server
    mcp.run(transport="stdio")