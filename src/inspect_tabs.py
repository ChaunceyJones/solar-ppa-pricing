"""
Lists every sheet name in the downloaded workbook, plus its dimensions and first-row preview —
deliberately done before writing any real loading code, since guessing which of 57 tabs holds
PPA price data (vs. metadata, vs. a chart-only tab) wastes time compared to just looking.

Usage:
    python src/inspect_tabs.py
"""

from pathlib import Path

import openpyxl

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
WORKBOOK_PATH = RAW_DIR / "utility_scale_solar_2025_data_update.xlsx"


if __name__ == "__main__":
    if not WORKBOOK_PATH.exists():
        raise SystemExit(
            f"{WORKBOOK_PATH} not found — run `python src/download_lbnl_data.py` first."
        )

    print(f"Opening {WORKBOOK_PATH.name} (this may take a moment for a 54 MB file)...")
    wb = openpyxl.load_workbook(WORKBOOK_PATH, read_only=True, data_only=True)

    print(f"\n{len(wb.sheetnames)} sheets found:\n")
    for name in wb.sheetnames:
        ws = wb[name]
        # .dimensions isn't available on ReadOnlyWorksheet (used automatically for large files
        # like this one) — max_row/max_column work in both modes.
        dims = f"{ws.max_row}x{ws.max_column}" if ws.max_row else "empty"
        # Grab the first row as a cheap peek at whether this looks like a data table or something
        # else (title page, chart-only sheet, notes).
        first_row = []
        for row in ws.iter_rows(min_row=1, max_row=1, values_only=True):
            first_row = [str(v)[:30] for v in row if v is not None][:6]
            break
        print(f"  {name!r:45} dims={dims:15} first_row={first_row}")

    wb.close()
    print("\nLook for tabs with names suggesting PPA price, project-level data, or pricing by "
          "region/technology — those are the candidates to load next.")
