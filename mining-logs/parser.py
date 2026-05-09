import re
import pandas as pd
from datetime import datetime
from pathlib import Path

def parse_qubic_log(log_text_or_file):
    """Parse real Qubic trainer logs"""
    if Path(log_text_or_file).exists():
        text = Path(log_text_or_file).read_text()
    else:
        text = log_text_or_file
    
    data = []
    current_seed = None
    
    for line in text.splitlines():
        if "Mining Seed:" in line:
            current_seed = line.split("Mining Seed:")[-1].strip()
        
        if "it/s" in line and "SHARES" in line:
            m = re.search(r'E:(\d+).*?SHARES:\s*(\d+)/(\d+).*?(\d+)\s*it/s.*?\s*(\d+)\s*avg it/s', line)
            if m:
                data.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'epoch': int(m.group(1)),
                    'shares_found': int(m.group(2)),
                    'shares_total': int(m.group(3)),
                    'it_s': int(m.group(4)),
                    'avg_it_s': int(m.group(5)),
                    'seed': current_seed,
                    'efficiency': round(int(m.group(2)) / int(m.group(3)), 4) if int(m.group(3)) > 0 else 0
                })
    
    df = pd.DataFrame(data)
    return df

# Quick usage
if __name__ == "__main__":
    print("Paste your mining log below (or save as mining-logs/example_log.txt)")
    # For now just show example
    print("Parser ready. Drop real logs into mining-logs/ and run this script.")
