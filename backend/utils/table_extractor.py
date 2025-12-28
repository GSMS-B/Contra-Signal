import pandas as pd
from typing import List, Dict, Optional, Any

class FinancialTableExtractor:
    def clean_dataframe(self, data: List[List[str]]) -> pd.DataFrame:
        """Converts list of lists to cleaned DataFrame."""
        if not data:
            return pd.DataFrame()
        
        # Assume first row is header
        headers = data[0]
        rows = data[1:]
        
        # Handle duplicate headers if any
        headers = [h if h else f"Col_{i}" for i, h in enumerate(headers)]
        
        df = pd.DataFrame(rows, columns=headers)
        return df

    def identify_financial_tables(self, tables: List[Dict[str, Any]]) -> Dict[str, pd.DataFrame]:
        """Heuristic to identify key statements."""
        identified = {
            'balance_sheet': None,
            'income_statement': None,
            'cash_flow': None
        }
        
        for table_info in tables:
            data = table_info['data']
            # Flatten to string to search keywords
            content_str = str(data).lower()
            
            df = self.clean_dataframe(data)
            
            # Simple keyword scoring
            if 'balance sheet' in content_str or ('assets' in content_str and 'liabilities' in content_str):
                if identified['balance_sheet'] is None: # take first match
                    identified['balance_sheet'] = df
            
            elif 'profit' in content_str and 'loss' in content_str and 'revenue' in content_str:
                if identified['income_statement'] is None:
                    identified['income_statement'] = df
            
            elif 'cash flow' in content_str and 'operating' in content_str:
                if identified['cash_flow'] is None:
                    identified['cash_flow'] = df
                    
        return identified

    def table_to_text(self, df: pd.DataFrame, table_type: str) -> str:
        """Converts table to LLM-readable text."""
        if df is None or df.empty:
            return ""
        
        return f"--- {table_type.replace('_', ' ').upper()} ---\n" + df.to_string()
