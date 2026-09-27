"""
The LevelTen & Trio 2024 PPA Index tab returned all-NaN with pandas' default header row —
a common symptom of a report-style tab with a title row and blank formatting rows before the
real table starts. This prints every raw row so we can see exactly where the real header is,
instead of guessing a skiprows value.

Usage:
    python src/peek_raw_rows.py "LevelTen & Trio 2024 PPA Index"
"""

import sys
from pathlib import Path

import openpyxl

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
WORKBOOK_PATH = RAW_DIR / "utility_scale_solar_2025_data_update.xlsx"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python src/peek_raw_rows.py "Sheet Name"')
    sheet_name = sys.argv[1]

    wb = openpyxl.load_workbook(WORKBOOK_PATH, read_only=True, data_only=True)
    ws = wb[sheet_name]

    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        # Only print rows that have at least one non-empty cell — skip fully blank rows silently
        # so the real structure isn't buried in noise, but still show the row number so skiprows
        # can be set correctly.
        if any(v is not None for v in row):
            print(f"row {i}: {row}")

    wb.close()
