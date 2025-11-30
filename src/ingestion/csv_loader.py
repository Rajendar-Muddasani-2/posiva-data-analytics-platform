"""
CSV Loader Module
Loads and validates CSV files
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Union
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CSVLoader:
    """
    Loader for CSV files with validation and type conversion
    """
    
    # Expected schema
    EXPECTED_COLUMNS = [
        'lot_id', 'wafer_id', 'device_id', 'test_num', 'test_name',
        'test_type', 'result', 'measured_value', 'lower_limit', 
        'upper_limit', 'units', 'bin', 'test_time_ms'
    ]
    
    REQUIRED_COLUMNS = [
        'lot_id', 'device_id', 'test_num', 'test_name', 'result'
    ]
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize CSV loader
        
        Args:
            strict_mode: If True, enforce strict schema validation
        """
        self.logger = logger
        self.strict_mode = strict_mode
    
    def load(
        self,
        file_path: Union[str, Path],
        validate: bool = True,
        infer_types: bool = True
    ) -> pd.DataFrame:
        """
        Load CSV file
        
        Args:
            file_path: Path to CSV file
            validate: Validate schema
            infer_types: Infer and convert data types
            
        Returns:
            Loaded DataFrame
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        self.logger.info(f"Loading CSV: {file_path.name}")
        
        try:
            # Load CSV
            df = pd.read_csv(file_path, low_memory=False)
            self.logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
            
            # Validate schema
            if validate:
                self._validate_schema(df, file_path.name)
            
            # Infer types
            if infer_types:
                df = self._infer_types(df)
            
            # Add derived columns
            df = self._add_derived_columns(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading CSV {file_path.name}: {e}")
            raise
    
    def _validate_schema(self, df: pd.DataFrame, filename: str):
        """Validate DataFrame schema"""
        # Check required columns
        missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            msg = f"Missing required columns in {filename}: {missing_cols}"
            if self.strict_mode:
                raise ValueError(msg)
            else:
                self.logger.warning(msg)
        
        # Check for unexpected columns
        if self.strict_mode:
            unexpected = set(df.columns) - set(self.EXPECTED_COLUMNS)
            if unexpected:
                self.logger.warning(f"Unexpected columns in {filename}: {unexpected}")
        
        self.logger.info(f"Schema validation passed for {filename}")
    
    def _infer_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Infer and convert data types"""
        # Numeric columns
        numeric_cols = [
            'test_num', 'measured_value', 'lower_limit', 
            'upper_limit', 'bin', 'test_time_ms'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # String columns
        string_cols = [
            'lot_id', 'wafer_id', 'device_id', 'test_name', 
            'test_type', 'result', 'units'
        ]
        
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(str)
        
        # Categorical columns (for memory efficiency)
        cat_cols = ['test_type', 'result', 'test_name']
        for col in cat_cols:
            if col in df.columns:
                df[col] = df[col].astype('category')
        
        return df
    
    def _add_derived_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived columns"""
        # is_fail flag
        if 'result' in df.columns:
            df['is_fail'] = (df['result'].str.lower() == 'fail').astype(int)
        
        # Test type flags
        if 'test_type' in df.columns:
            df['is_parametric'] = (df['test_type'].str.lower() == 'parametric').astype(int)
            df['is_functional'] = (df['test_type'].str.lower() == 'functional').astype(int)
        
        # Margin calculation (for parametric tests)
        if all(col in df.columns for col in ['measured_value', 'lower_limit', 'upper_limit', 'test_type']):
            def calculate_margin(row):
                if row.get('test_type', '').lower() != 'parametric':
                    return np.nan
                
                val = row['measured_value']
                lo = row['lower_limit']
                hi = row['upper_limit']
                
                if pd.isna(val):
                    return np.nan
                
                if not pd.isna(lo) and not pd.isna(hi):
                    # Two-sided limit
                    if hi != lo:
                        margin_lo = (val - lo) / (hi - lo)
                        margin_hi = (hi - val) / (hi - lo)
                        return min(margin_lo, margin_hi)
                elif not pd.isna(lo):
                    # Lower limit only
                    return (val - lo) / abs(lo) if lo != 0 else 0
                elif not pd.isna(hi):
                    # Upper limit only
                    return (hi - val) / abs(hi) if hi != 0 else 0
                
                return np.nan
            
            df['margin'] = df.apply(calculate_margin, axis=1)
        
        return df
    
    def load_directory(
        self,
        directory: Union[str, Path],
        pattern: str = "*.csv",
        **kwargs
    ) -> pd.DataFrame:
        """
        Load all CSV files in a directory
        
        Args:
            directory: Directory path
            pattern: File pattern to match
            **kwargs: Arguments passed to load()
            
        Returns:
            Combined DataFrame
        """
        directory = Path(directory)
        files = list(directory.glob(pattern))
        
        if not files:
            self.logger.warning(f"No CSV files found in {directory}")
            return pd.DataFrame()
        
        self.logger.info(f"Found {len(files)} CSV files to load")
        
        dfs = []
        for file_path in files:
            try:
                df = self.load(file_path, **kwargs)
                dfs.append(df)
            except Exception as e:
                self.logger.error(f"Failed to load {file_path.name}: {e}")
        
        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            self.logger.info(f"Combined {len(dfs)} files into {len(combined)} records")
            return combined
        else:
            return pd.DataFrame()
    
    def save_to_parquet(self, df: pd.DataFrame, output_path: Union[str, Path]):
        """
        Save DataFrame to Parquet format
        
        Args:
            df: DataFrame to save
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_parquet(output_path, index=False, compression='snappy')
        self.logger.info(f"Saved {len(df)} records to {output_path}")
    
    @staticmethod
    def create_sample_csv(output_path: Union[str, Path], n_devices: int = 100):
        """
        Create a sample CSV file for testing
        
        Args:
            output_path: Output file path
            n_devices: Number of devices to generate
        """
        np.random.seed(42)
        
        records = []
        lot_id = "LOT001"
        wafer_id = "W01"
        
        for device_idx in range(n_devices):
            device_id = f"D{device_idx:04d}"
            
            # Generate 10 tests per device
            for test_idx in range(10):
                test_num = test_idx + 1
                test_name = f"TEST_{test_num}"
                test_type = "parametric" if test_idx < 7 else "functional"
                
                # Simulate results
                if test_type == "parametric":
                    nominal = 100 + test_idx * 10
                    measured_value = np.random.normal(nominal, 5)
                    lower_limit = nominal - 20
                    upper_limit = nominal + 20
                    result = "pass" if lower_limit <= measured_value <= upper_limit else "fail"
                    units = "mV"
                else:
                    measured_value = np.nan
                    lower_limit = np.nan
                    upper_limit = np.nan
                    result = "pass" if np.random.random() > 0.05 else "fail"
                    units = ""
                
                bin_num = 1 if result == "pass" else np.random.randint(2, 10)
                test_time = np.random.uniform(10, 100)
                
                records.append({
                    'lot_id': lot_id,
                    'wafer_id': wafer_id,
                    'device_id': device_id,
                    'test_num': test_num,
                    'test_name': test_name,
                    'test_type': test_type,
                    'result': result,
                    'measured_value': measured_value,
                    'lower_limit': lower_limit,
                    'upper_limit': upper_limit,
                    'units': units,
                    'bin': bin_num,
                    'test_time_ms': test_time
                })
        
        df = pd.DataFrame(records)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        
        print(f"✅ Created sample CSV: {output_path}")
        print(f"   Devices: {n_devices}, Total records: {len(df)}")
