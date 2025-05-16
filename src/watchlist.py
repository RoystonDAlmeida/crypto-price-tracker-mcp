"""
Watchlist manager for tracking cryptocurrency symbols
"""
from datetime import datetime
from typing import Dict, List, Optional
import json
import os


class WatchlistManager:
    """Manager for cryptocurrency watchlist"""
    
    def __init__(self, storage_file: str = "watchlist.json"):
        """
        Initialize the watchlist manager
        
        Args:
            storage_file: Path to the JSON file for storing watchlist data
        """
        self.storage_file = storage_file
        self.watchlist = self._load_watchlist()
    
    def _load_watchlist(self) -> Dict[str, str]:
        """
        Load watchlist from storage file
        
        Returns:
            Dictionary mapping coin symbols to date added
        """
        if not os.path.exists(self.storage_file):
            return {}
        
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading watchlist: {e}")
            return {}

    def add_coin(self, symbol: str) -> bool:
        """
        Add a coin to the watchlist
        
        Args:
            symbol: The cryptocurrency symbol to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        # Normalize symbol to uppercase
        symbol = symbol.upper()
        
        # Add to watchlist if not already present
        if symbol not in self.watchlist:
            self.watchlist[symbol] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return self._save_watchlist()
        
        return True
    
    def _save_watchlist(self) -> bool:
        """
        Save watchlist to storage file
        
        Returns:
            True if save was successful, False otherwise
        """
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.watchlist, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving watchlist: {e}")
            return False
    
    def get_watchlist(self) -> Dict[str, str]:
        """
        Get the current watchlist
        
        Returns:
            Dictionary mapping coin symbols to date added
        """
        return self.watchlist
    
    # def remove_coin(self, symbol: str) -> bool:
    #     """
    #     Remove a coin from the watchlist
        
    #     Args:
    #         symbol: The cryptocurrency symbol to remove
            
    #     Returns:
    #         True if removal was successful, False otherwise
    #     """
    #     # Normalize symbol to uppercase
    #     symbol = symbol.upper()
        
    #     # Remove from watchlist if present
    #     if symbol in self.watchlist:
    #         del self.watchlist[symbol]
    #         return self._save_watchlist()
        
    #     return False
    
    # def is_in_watchlist(self, symbol: str) -> bool:
    #     """
    #     Check if a coin is in the watchlist
        
    #     Args:
    #         symbol: The cryptocurrency symbol to check
            
    #     Returns:
    #         True if coin is in watchlist, False otherwise
    #     """
    #     # Normalize symbol to uppercase
    #     symbol = symbol.upper()
        
    #     return symbol in self.watchlist
    
    # def clear_watchlist(self) -> bool:
    #     """
    #     Clear the entire watchlist
        
    #     Returns:
    #         True if clearing was successful, False otherwise
    #     """
    #     self.watchlist = {}
    #     return self._save_watchlist()
    
    # def import_from_list(self, symbols: List[str]) -> int:
    #     """
    #     Import multiple coins into the watchlist
        
    #     Args:
    #         symbols: List of cryptocurrency symbols to add
            
    #     Returns:
    #         Number of coins added
    #     """
    #     count = 0
        
    #     for symbol in symbols:
    #         symbol = symbol.upper()
    #         if symbol not in self.watchlist:
    #             self.watchlist[symbol] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #             count += 1
        
    #     if count > 0:
    #         self._save_watchlist()
        
    #     return count