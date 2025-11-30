#!/usr/bin/env python3
"""
Generate sample test data for POSIVA platform
Standalone script - doesn't require dependencies
"""

import csv
import random
from pathlib import Path

def generate_sample_data(output_path: str, n_devices: int = 200):
    """Generate sample CSV data"""
    
    random.seed(42)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    records = []
    lot_id = "LOT001"
    wafer_id = "W01"
    
    print(f"Generating sample data...")
    
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
                measured_value = random.gauss(nominal, 5)
                lower_limit = nominal - 20
                upper_limit = nominal + 20
                result = "pass" if lower_limit <= measured_value <= upper_limit else "fail"
                units = "mV"
            else:
                measured_value = ""
                lower_limit = ""
                upper_limit = ""
                result = "pass" if random.random() > 0.05 else "fail"
                units = ""
            
            bin_num = 1 if result == "pass" else random.randint(2, 10)
            test_time = random.uniform(10, 100)
            
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
    
    # Write to CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    
    print(f"✅ Created sample CSV: {output_path}")
    print(f"   Devices: {n_devices}, Total records: {len(records)}")
    print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    generate_sample_data("data/sample/sample_data.csv", n_devices=200)
