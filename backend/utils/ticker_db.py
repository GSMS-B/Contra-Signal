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
        """Loads and cleans the CSV data into memory."""
        if not os.path.exists(filepath):
            logger.error(f"Stock data file not found at: {filepath}")
            return

        try:
            # Read CSV with flexible encoding
            try:
                self.df = pd.read_csv(filepath, encoding='utf-8')
            except UnicodeDecodeError:
                self.df = pd.read_csv(filepath, encoding='latin1')
            
            # Clean column names
            self.df.columns = self.df.columns.str.strip()
            
            # Ensure required columns
            if 'Name' not in self.df.columns:
                logger.error("CSV missing required 'Name' column.")
                self.df = None
                return

            # Clean Name column
            self.df['Name'] = self.df['Name'].astype(str).str.strip()
            
            # Numeric cleaning for all metric columns
            # We explicitly clean these columns to be usable floats
            numeric_cols = [
                'LTP', 'Change(%)', 'Open', 'Volume', 'Market Cap (Cr.)', 
                'PE Ratio', 'Industry PE', '52W High', '52W Low', 
                '1M Returns', '3M Returns', '1 Yr Returns', '3 Yr Returns', '5 Yr Returns',
                'PB Ratio', 'Dividend', 'ROE', 'ROCE', 'EPS', 
                '50 DMA', '200 DMA', 'RSI', 'Margin Funding', 'Margin Pledge'
            ]
            
            for col in numeric_cols:
                if col in self.df.columns:
                    # Remove commas, %, and whitespace, then coerce to numeric
                    # Force string conversion first to handle mixed types safely
                    self.df[col] = (
                        self.df[col]
                        .astype(str)
                        .str.replace(',', '', regex=False)
                        .str.replace('%', '', regex=False)
                        .str.strip()
                    )
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0.0)

            logger.info(f"Loaded {len(self.df)} tickers from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to load stock data: {e}")
            self.df = None

    def search_names(self, query: str, limit: int = 10):
        """Searches for company names containing the query string (case-insensitive)."""
        if self.df is None or not query:
            return []
        
        try:
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
        
        mask = self.df['Name'].str.lower() == name.strip().lower()
        return mask.any()

    def get_company_details(self, name: str) -> dict:
        """Returns the full row of data for a given company name."""
        if self.df is None or not name:
            return None
        
        try:
            # Case-insensitive exact match
            row = self.df[self.df['Name'].str.lower() == name.strip().lower()]
            if row.empty:
                return None
            
            # Convert to dictionary and handle Nan/Inf for JSON serialization
            data = row.iloc[0].to_dict()
            return data
        except Exception as e:
            logger.error(f"Error getting details for {name}: {e}")
            return None

    def get_peers_by_industry(self, industry_pe: float, exclude_name: str, limit: int = 5) -> list:
        """
        Finds peers with the same or similar Industry PE.
        This uses the logic: Same Industry PE = Same Sector/Industry.
        """
        if self.df is None or industry_pe == 0:
            return []
        
        try:
            # Filter by matching Industry PE
            # Using a small tolerance just in case of float weirdness, though exact match is requested
            peers = self.df[
                (self.df['Industry PE'] >= industry_pe - 0.1) & 
                (self.df['Industry PE'] <= industry_pe + 0.1) &
                (self.df['Name'].str.lower() != exclude_name.lower())
            ]
            
            # Use 'Market Cap (Cr.)' for sorting if available, else random slice
            if 'Market Cap (Cr.)' in self.df.columns:
                peers = peers.sort_values(by='Market Cap (Cr.)', ascending=False)

            return peers.head(limit).to_dict('records')
        except Exception as e:
            logger.error(f"Error finding peers: {e}")
            return []

# Global instance accessor
def get_ticker_db():
    return TickerDatabase()
