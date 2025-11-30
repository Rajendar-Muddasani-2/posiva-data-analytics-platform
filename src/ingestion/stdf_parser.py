"""
STDF Parser Module
Parses Standard Test Data Format (STDF) files from ATE
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Union
from src.utils.logger import get_logger

logger = get_logger(__name__)


class STDFParser:
    """
    Parser for STDF (Standard Test Data Format) files
    
    STDF is a binary format used by semiconductor ATE equipment.
    This parser converts STDF to pandas DataFrame.
    """
    
    def __init__(self):
        """Initialize STDF parser"""
        self.logger = logger
        self._check_pystdf()
    
    def _check_pystdf(self):
        """Check if pystdf is available"""
        try:
            import pystdf
            self.pystdf = pystdf
            self.has_pystdf = True
        except ImportError:
            self.logger.warning("pystdf not installed. STDF parsing will be limited.")
            self.has_pystdf = False
    
    def parse(
        self,
        file_path: Union[str, Path],
        include_parametric: bool = True,
        include_functional: bool = True
    ) -> pd.DataFrame:
        """
        Parse STDF file to DataFrame
        
        Args:
            file_path: Path to STDF file
            include_parametric: Include parametric test results
            include_functional: Include functional test results
            
        Returns:
            DataFrame with parsed test results
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"STDF file not found: {file_path}")
        
        self.logger.info(f"Parsing STDF file: {file_path.name}")
        
        if self.has_pystdf:
            return self._parse_with_pystdf(file_path, include_parametric, include_functional)
        else:
            self.logger.error("pystdf required for STDF parsing. Install: pip install pystdf")
            raise ImportError("pystdf not available")
    
    def _parse_with_pystdf(
        self,
        file_path: Path,
        include_parametric: bool,
        include_functional: bool
    ) -> pd.DataFrame:
        """Parse STDF using pystdf library"""
        from pystdf.IO import Parser
        
        records = []
        lot_info = {}
        wafer_info = {}
        test_info = {}
        
        try:
            with file_path.open('rb') as f:
                parser = Parser(inp=f)
                
                for rec in parser:
                    rec_type = type(rec).__name__
                    
                    # Master Information Record (MIR) - Lot level
                    if rec_type == 'Mir':
                        lot_info = {
                            'lot_id': getattr(rec, 'LOT_ID', None),
                            'part_typ': getattr(rec, 'PART_TYP', None),
                            'node_nam': getattr(rec, 'NODE_NAM', None),
                            'tstr_typ': getattr(rec, 'TSTR_TYP', None),
                            'job_nam': getattr(rec, 'JOB_NAM', None),
                            'oper_nam': getattr(rec, 'OPER_NAM', None),
                        }
                    
                    # Wafer Information Record (WIR)
                    elif rec_type == 'Wir':
                        wafer_info = {
                            'wafer_id': getattr(rec, 'WAFER_ID', None),
                            'head_num': getattr(rec, 'HEAD_NUM', None),
                            'site_grp': getattr(rec, 'SITE_GRP', None),
                        }
                    
                    # Part Information Record (PIR) - Device start
                    elif rec_type == 'Pir':
                        current_device = {
                            'head_num': getattr(rec, 'HEAD_NUM', None),
                            'site_num': getattr(rec, 'SITE_NUM', None),
                        }
                    
                    # Parametric Test Record (PTR)
                    elif rec_type == 'Ptr' and include_parametric:
                        result = {
                            'lot_id': lot_info.get('lot_id'),
                            'wafer_id': wafer_info.get('wafer_id'),
                            'part_id': getattr(rec, 'PART_ID', None),
                            'test_num': getattr(rec, 'TEST_NUM', None),
                            'test_name': getattr(rec, 'TEST_TXT', ''),
                            'test_type': 'parametric',
                            'result': 'pass' if getattr(rec, 'TEST_FLG', 0) & 0x80 == 0 else 'fail',
                            'measured_value': getattr(rec, 'RESULT', np.nan),
                            'lower_limit': getattr(rec, 'LO_LIMIT', np.nan),
                            'upper_limit': getattr(rec, 'HI_LIMIT', np.nan),
                            'units': getattr(rec, 'UNITS', ''),
                            'test_time_ms': getattr(rec, 'TEST_T', 0) * 1000,  # Convert to ms
                        }
                        records.append(result)
                    
                    # Functional Test Record (FTR)
                    elif rec_type == 'Ftr' and include_functional:
                        result = {
                            'lot_id': lot_info.get('lot_id'),
                            'wafer_id': wafer_info.get('wafer_id'),
                            'part_id': getattr(rec, 'PART_ID', None),
                            'test_num': getattr(rec, 'TEST_NUM', None),
                            'test_name': getattr(rec, 'TEST_TXT', ''),
                            'test_type': 'functional',
                            'result': 'pass' if getattr(rec, 'TEST_FLG', 0) & 0x80 == 0 else 'fail',
                            'measured_value': np.nan,
                            'lower_limit': np.nan,
                            'upper_limit': np.nan,
                            'units': '',
                            'test_time_ms': getattr(rec, 'TEST_T', 0) * 1000,
                        }
                        records.append(result)
                    
                    # Part Results Record (PRR) - Device results
                    elif rec_type == 'Prr':
                        # Add bin information to last device tests
                        hard_bin = getattr(rec, 'HARD_BIN', None)
                        soft_bin = getattr(rec, 'SOFT_BIN', None)
                        x_coord = getattr(rec, 'X_COORD', None)
                        y_coord = getattr(rec, 'Y_COORD', None)
                        
                        # Update records for this device
                        # (In production, would track by device_id)
            
            # Convert to DataFrame
            df = pd.DataFrame(records)
            
            if len(df) > 0:
                # Add derived columns
                df['device_id'] = df['part_id']
                df['is_fail'] = (df['result'] == 'fail').astype(int)
                df['is_parametric'] = (df['test_type'] == 'parametric').astype(int)
                df['is_functional'] = (df['test_type'] == 'functional').astype(int)
                
                # Calculate margin for parametric tests
                def calculate_margin(row):
                    if row['test_type'] != 'parametric' or pd.isna(row['measured_value']):
                        return np.nan
                    
                    val = row['measured_value']
                    lo = row['lower_limit']
                    hi = row['upper_limit']
                    
                    if not pd.isna(lo) and not pd.isna(hi):
                        # Two-sided limit
                        margin_lo = (val - lo) / (hi - lo) if hi != lo else 0
                        margin_hi = (hi - val) / (hi - lo) if hi != lo else 0
                        return min(margin_lo, margin_hi)
                    elif not pd.isna(lo):
                        # Lower limit only
                        return (val - lo) / abs(lo) if lo != 0 else 0
                    elif not pd.isna(hi):
                        # Upper limit only
                        return (hi - val) / abs(hi) if hi != 0 else 0
                    return np.nan
                
                df['margin'] = df.apply(calculate_margin, axis=1)
                
                self.logger.info(f"Parsed {len(df)} test results from {len(df['device_id'].unique())} devices")
            else:
                self.logger.warning("No test results found in STDF file")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error parsing STDF file: {e}")
            raise
    
    def parse_directory(
        self,
        directory: Union[str, Path],
        pattern: str = "*.stdf",
        **kwargs
    ) -> pd.DataFrame:
        """
        Parse all STDF files in a directory
        
        Args:
            directory: Directory containing STDF files
            pattern: File pattern to match
            **kwargs: Arguments passed to parse()
            
        Returns:
            Combined DataFrame
        """
        directory = Path(directory)
        files = list(directory.glob(pattern))
        
        if not files:
            self.logger.warning(f"No STDF files found in {directory}")
            return pd.DataFrame()
        
        self.logger.info(f"Found {len(files)} STDF files to parse")
        
        dfs = []
        for file_path in files:
            try:
                df = self.parse(file_path, **kwargs)
                dfs.append(df)
            except Exception as e:
                self.logger.error(f"Failed to parse {file_path.name}: {e}")
        
        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            self.logger.info(f"Combined {len(dfs)} files into {len(combined)} records")
            return combined
        else:
            return pd.DataFrame()
    
    def save_to_parquet(self, df: pd.DataFrame, output_path: Union[str, Path]):
        """
        Save parsed data to Parquet format
        
        Args:
            df: DataFrame to save
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_parquet(output_path, index=False, compression='snappy')
        self.logger.info(f"Saved {len(df)} records to {output_path}")
