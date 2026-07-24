import csv
import io
from typing import List, Dict, Any

class ExportService:
    """
    Service responsible for exporting data structures to formatted files (CSV, Excel, PDF).
    """

    @staticmethod
    def generate_csv(headers: List[str], data: List[Dict[str, Any]]) -> str:
        """
        Generate CSV string from header list and row dictionaries.
        """
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers, extrasaction="ignore")
        
        writer.writeheader()
        for row in data:
            writer.writerow(row)
            
        return output.getvalue()
