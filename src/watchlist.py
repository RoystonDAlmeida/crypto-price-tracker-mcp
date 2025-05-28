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
            Dictionary mapping coin ids to date added
        """
        if not os.path.exists(self.storage_file):
            return {}
        
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading watchlist: {e}")
            return {}

    def add_coin(self, id: str) -> bool:
        """
        Add a coin to the watchlist
        
        Args:
            id: The cryptocurrency id to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        # Normalize id to uppercase
        id = id.lower()
        
        # Add to watchlist if not already present
        if id not in self.watchlist:
            self.watchlist[id] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
            Dictionary mapping coin ids to date added
        """

        return self.watchlist
    
    def remove_coin(self, id: str) -> bool:
        """
        Remove a coin from the watchlist
        
        Args:
            symbol: The cryptocurrency id to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        
        # Normalize id to lowercase
        id = id.lower()
        
        # Remove from watchlist if present
        if id in self.watchlist:
            del self.watchlist[id]
            return self._save_watchlist()
        
        return False