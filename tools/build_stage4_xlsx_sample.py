from __future__ import annotations

import csv
import sys
from pathlib import Path

from openpyxl import Workbook


SHEETS = [
    ("orders.csv", "Orders"),
    ("inventory.csv", "Inventory"),
    ("fulfillments.csv", "Fulfillments"),
    ("refunds.csv", "Refunds"),
]


def append_csv_sheet(workbook: Workbook, csv_path: Path, sheet_name: str) -> None:
    worksheet = workbook.create_sheet(title=sheet_name)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        for row in reader:
            worksheet.append(row)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: build_stage4_xlsx_sample.py <sample_dir> <output.xlsx>")
        return 2
    sample_dir = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    workbook = Workbook()
    default_sheet = workbook.active
    workbook.remove(default_sheet)
    for csv_name, sheet_name in SHEETS:
        append_csv_sheet(workbook, sample_dir / csv_name, sheet_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
