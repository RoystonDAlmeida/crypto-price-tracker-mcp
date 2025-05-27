"""
API client for fetching cryptocurrency data from CoinGecko API
"""

import httpx
import json
import asyncio
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

class CryptoApiClient:
    """Client for fetching cryptocurrency data from CoinGecko API"""
    
    def __init__(self):
        """Initialize the API client with base URL and headers"""

        self.base_url = os.getenv("COINGECKO_BASE_URL")
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "MCP Crypto Price Tracker"
        }

        # Cache for storing recent responses to avoid rate limiting
        self.cache = {}
        self.cache_ttl = 60  # Cache TTL in seconds
    
    async def get_supported_coins(self) -> Optional[List[Dict[str, str]]]:
        """
        Get list of supported coins from CoinGecko
        
        Returns:
            List of supported coins or None if request failed
        """
        try:
            # Check cache first
            cache_key = "supported_coins"
            current_time = datetime.now().timestamp()
            
            if cache_key in self.cache and (current_time - self.cache[cache_key]['timestamp'] < self.cache_ttl):
                return self.cache[cache_key]['data']
            
            # Construct URL for CoinGecko API
            url = f"{self.base_url}/coins/list"
            
            # Make request to CoinGecko API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    print(f"Error fetching supported coins: {response.status_code}")
                    return None
                
                data = response.json()
                
                # Update cache
                self.cache[cache_key] = {
                    'timestamp': current_time,
                    'data': data
                }
                
                return data
                
        except Exception as e:
            print(f"Error fetching supported coins: {e}")
            return None
        
    async def get_current_price(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Get current price data for a cryptocurrency
        
        Args:
            symbol: The cryptocurrency ID (e.g., bitcoin, ethereum)
            
        Returns:
            Dictionary with price data or None if request failed
        """

        # Normalize input symbol to lowercase
        normalized_input = id.lower()
        coin_id_to_use = normalized_input  # Default to using the normalized input as ID

        supported_coins_list = await self.get_supported_coins()
        
        if supported_coins_list:
            # Step 1: Check if the normalized_input is a direct ID match
            is_direct_id_match = False
            for coin_info in supported_coins_list:
                if coin_info['id'] == normalized_input:
                    # coin_id_to_use is already normalized_input, this confirms it.
                    # No change to coin_id_to_use needed here as it's already correct.
                    is_direct_id_match = True
                    break
        else:
            # If fetching supported coins failed, we'll use the normalized_input directly.
            print(f"Warning: Could not retrieve supported coins list. Using '{normalized_input}' as coin ID for price fetching for input '{id}'.")

        try:
            # Construct URL for CoinGecko API
            url = f"{self.base_url}/coins/{coin_id_to_use}"
            
            # Check cache first
            cache_key = f"price_{coin_id_to_use}"
            current_time = datetime.now().timestamp()
            
            if cache_key in self.cache and (current_time - self.cache[cache_key]['timestamp'] < self.cache_ttl):
                return self.cache[cache_key]['data']
            
            # Make request to CoinGecko API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params={"localization": "false", "tickers": "false", "market_data": "true"},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    print(f"Error fetching price for {coin_id_to_use} (input: {id}): {response.status_code} - {response.text}")
                    return None
                
                data = response.json()
                
                # Ensure market_data and current_price exist before accessing
                if "market_data" not in data or \
                   "current_price" not in data["market_data"] or \
                   "usd" not in data["market_data"]["current_price"]:
                    print(f"Error: Unexpected data structure for {coin_id_to_use} (input: {id}). 'market_data.current_price.usd' not found. Response: {data}")
                    return None

                # Extract relevant price data
                price_data = {
                    "price": data["market_data"]["current_price"]["usd"],
                    "change_24h": data["market_data"].get("price_change_percentage_24h"),
                    "last_updated": data.get("last_updated"),
                    "name": data.get("name", coin_id_to_use),
                    "symbol": data.get("symbol", id).upper() # Fallback to original input symbol if not in response
                }
                # Update cache
                self.cache[cache_key] = {
                    'timestamp': current_time,
                    'data': price_data
                }
                
                return price_data

        except httpx.RequestError as e:
            print(f"HTTP request error fetching price for {coin_id_to_use} (input: {id}): {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error fetching price for {coin_id_to_use} (input: {id}): {e}")
            return None
        except KeyError as e:
            print(f"KeyError: Missing expected key '{e}' in API response for {coin_id_to_use} (input: {id}).")
            return None
        except Exception as e:
            print(f"Generic error fetching price for {coin_id_to_use} (input: {id}): {e}")
            return None
    
    # async def get_price_history(self, symbol: str, timeframe: str) -> Optional[List[Dict[str, Any]]]:
    #     """
    #     Get historical price data for a cryptocurrency
        
    #     Args:
    #         symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    #         timeframe: The time period (e.g., 7d, 30d, 90d, 1y)
            
    #     Returns:
    #         List of price data points or None if request failed
    #     """
    #     # Normalize symbol
    #     symbol = symbol.lower()
        
    #     # Try to map common symbols to CoinGecko IDs
    #     symbol_mapping = {
    #         "btc": "bitcoin",
    #         "eth": "ethereum",
    #         "usdt": "tether",
    #         "bnb": "binancecoin",
    #         "sol": "solana",
    #         "xrp": "ripple",
    #         "ada": "cardano",
    #         "doge": "dogecoin",
    #         "dot": "polkadot",
    #         "ltc": "litecoin"
    #     }
        
    #     coin_id = symbol_mapping.get(symbol, symbol)
        
    #     # Map timeframe to days
    #     days_mapping = {
    #         "1d": "1",
    #         "7d": "7",
    #         "14d": "14",
    #         "30d": "30",
    #         "90d": "90",
    #         "180d": "180",
    #         "1y": "365",
    #         "max": "max"
    #     }
        
    #     # Default to 7 days if timeframe not recognized
    #     days = days_mapping.get(timeframe.lower(), "7")
        
    #     try:
    #         # Check cache first
    #         cache_key = f"history_{coin_id}_{days}"
    #         current_time = datetime.now().timestamp()
            
    #         if cache_key in self.cache and (current_time - self.cache[cache_key]['timestamp'] < self.cache_ttl):
    #             return self.cache[cache_key]['data']
            
    #         # Construct URL for CoinGecko API
    #         url = f"{self.base_url}/coins/{coin_id}/market_chart"
            
    #         # Make request to CoinGecko API
    #         async with httpx.AsyncClient() as client:
    #             response = await client.get(
    #                 url,
    #                 headers=self.headers,
    #                 params={"vs_currency": "usd", "days": days},
    #                 timeout=10.0
    #             )
                
    #             if response.status_code != 200:
    #                 print(f"Error fetching history for {coin_id}: {response.status_code}")
    #                 return None
                
    #             data = response.json()
                
    #             # Process price data
    #             history_data = []
    #             for timestamp, price in data["prices"]:
    #                 date = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
    #                 history_data.append({
    #                     "date": date,
    #                     "price": round(price, 2)
    #                 })
                
    #             # Reduce data points to avoid overwhelming response
    #             if len(history_data) > 30:
    #                 step = len(history_data) // 30
    #                 history_data = history_data[::step]
                
    #             # Update cache
    #             self.cache[cache_key] = {
    #                 'timestamp': current_time,
    #                 'data': history_data
    #             }
                
    #             return history_data
                
    #     except Exception as e:
    #         print(f"Error fetching history for {coin_id}: {e}")
    #         return None
    
    
    # async def search_coins(self, query: str) -> Optional[List[Dict[str, str]]]:
    #     """
    #     Search for coins by name or symbol
        
    #     Args:
    #         query: Search query string
            
    #     Returns:
    #         List of matching coins or None if request failed
    #     """
    #     try:
    #         supported_coins = await self.get_supported_coins()
            
    #         if not supported_coins:
    #             return None
            
    #         # Perform case-insensitive search
    #         query = query.lower()
    #         matches = [
    #             coin for coin in supported_coins
    #             if query in coin["id"].lower() or query in coin["symbol"].lower() or query in coin["name"].lower()
    #         ]
            
    #         # Limit results
    #         return matches[:10] if matches else []
            
    #     except Exception as e:
    #         print(f"Error searching coins: {e}")
    #         return None