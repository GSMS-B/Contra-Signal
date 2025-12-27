import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

class TickerDatabase:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TickerDatabase, cls).__new__(cls)
            cls._instance.df = None
        return cls._instance

    def load_data(self, filepath: str):
        """Loads the CSV data into memory."""
        if not os.path.exists(filepath):
            logger.error(f"Stock data file not found at: {filepath}")
            return

        try:
            # Read CSV
            # Using 'latin1' or 'utf-8' encoding usually works for stock data; 'utf-8' is standard.
            # Handle potential encoding errors safely.
            try:
                self.df = pd.read_csv(filepath, encoding='utf-8')
            except UnicodeDecodeError:
                self.df = pd.read_csv(filepath, encoding='latin1')
            
            # Clean column names (strip whitespace)
            self.df.columns = self.df.columns.str.strip()
            
            # Ensure 'Name' column exists
            if 'Name' not in self.df.columns:
                logger.error("CSV missing required 'Name' column.")
                self.df = None
                return

            # Clean Name column: strip whitespace, ensure string
            self.df['Name'] = self.df['Name'].astype(str).str.strip()
            
            logger.info(f"Loaded {len(self.df)} tickers from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to load stock data: {e}")
            self.df = None

    def search_names(self, query: str, limit: int = 10):
        """
        Searches for company names containing the query string (case-insensitive).
        Returns a list of matching names.
        """
        if self.df is None or not query:
            return []
        
        try:
            # Case-insensitive containment check
            # We use 'na=False' to handle any potential NaNs that slipped through
            mask = self.df['Name'].str.contains(query, case=False, na=False)
            matches = self.df.loc[mask, 'Name'].head(limit).tolist()
            return matches
        except Exception as e:
            logger.error(f"Error filtering names: {e}")
            return []

    def validate_name(self, name: str) -> bool:
        """Checks if a company name exists in the database (exact match, case-insensitive)."""
        if self.df is None or not name:
            return False
        
        # Case-insensitive match
        mask = self.df['Name'].str.lower() == name.strip().lower()
        return mask.any()

# Global instance accessor
def get_ticker_db():
    return TickerDatabase()
