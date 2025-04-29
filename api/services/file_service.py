import pandas as pd
from typing import Optional

async def process_uploaded_file(file_path: str, file_type: str, **kwargs) -> pd.DataFrame:
    """
    Process an uploaded file and return a pandas DataFrame.
    Supports CSV, Excel, and JSON formats.
    """
    if file_type.lower() == 'csv' or file_path.endswith('.csv'):
        return pd.read_csv(file_path, **kwargs)
    elif file_type.lower() == 'json' or file_path.endswith('.json'):
        return pd.read_json(file_path, **kwargs)
    elif file_type.lower() in ['xlsx', 'xls'] or file_path.endswith(('.xlsx', '.xls')):
        return pd.read_excel(file_path, **kwargs)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
