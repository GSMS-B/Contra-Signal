import sys
import os

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber is not installed. Please run: pip install pdfplumber")
    sys.exit(1)

def parse_pdf(pdf_path):
    """
    Parses a PDF file and prints its content and tables to the console using pdfplumber.
    
    Args:
        pdf_path (str): The file path to the PDF.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    try:
        print(f"--- Started parsing: {pdf_path} ---")
        
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Total Pages: {len(pdf.pages)}\n")
            
            for i, page in enumerate(pdf.pages):
                print(f"--- Page {i + 1} ---")
                
                # Extract Text
                text = page.extract_text()
                if text:
                    print("[Text Content]:")
                    print(text)
                else:
                    print("[No text found on this page]")
                
                print("\n[Table Content]:")
                # Extract Tables
                tables = page.extract_tables()
                
                if tables:
                    for j, table in enumerate(tables):
                        print(f"  Table {j + 1}:")
                        for row in table:
                            # Filter out None values and clean up the row string
                            clean_row = [str(cell).strip() if cell is not None else "" for cell in row]
                            print(f"    {clean_row}")
                        print("") 
                else:
                    print("  No tables found.")
                
                print("-" * 20)
                
        print("\n--- Finished parsing ---")
        
    except Exception as e:
        print(f"An error occurred while parsing the PDF: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_pdf.py <path_to_pdf>")
        user_input = input("Or enter path to PDF here: ").strip()
        if user_input:
            parse_pdf(user_input)
    else:
        parse_pdf(sys.argv[1])
