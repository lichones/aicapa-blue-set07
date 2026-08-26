from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SOURCE_CSV = BASE_DIR / "모집공고.csv"
SPLIT_DIR = BASE_DIR / "분야별_csv"
SUMMARY_CSV = BASE_DIR / "결과_분야집계.csv"
WEB_DATA_JS = BASE_DIR / "data.js"
REQUIRED_COLUMNS = (
    "공고ID",
    "프로그램명",
    "분야",
    "지역",
    "모집인원",
    "활동요일",
    "마감일",
    "상태",
)


def safe_filename(value: str) -> str:
    """Windows에서도 안전한 분야별 CSV 파일명을 만든다."""
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value.strip())
    return cleaned or "미분류"


def load_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = reader.fieldnames or []
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing:
            raise ValueError(f"필수 컬럼 누락: {', '.join(missing)}")
        rows = list(reader)

    for line_number, row in enumerate(rows, start=2):
        try:
            headcount = int(row["모집인원"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{line_number}행 모집인원이 정수가 아닙니다.") from exc
        if headcount < 0:
            raise ValueError(f"{line_number}행 모집인원이 음수입니다.")
    return fieldnames, rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    fieldnames, rows = load_rows(SOURCE_CSV)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["분야"].strip() or "미분류"].append(row)

    SPLIT_DIR.mkdir(exist_ok=True)
    expected_files: set[Path] = set()
    summary_rows: list[dict[str, object]] = []

    for category in sorted(grouped):
        category_rows = grouped[category]
        output_path = SPLIT_DIR / f"모집공고_{safe_filename(category)}.csv"
        expected_files.add(output_path.resolve())
        write_csv(output_path, fieldnames, category_rows)
        summary_rows.append(
            {
                "분야": category,
                "공고건수": len(category_rows),
                "총모집인원": sum(int(row["모집인원"]) for row in category_rows),
            }
        )

    # 이전 실행에서 남은 분야 파일이 잘못 제출되지 않도록 이 도구가 만든 패턴만 정리한다.
    for old_path in SPLIT_DIR.glob("모집공고_*.csv"):
        if old_path.resolve() not in expected_files:
            old_path.unlink()

    with SUMMARY_CSV.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["분야", "공고건수", "총모집인원"])
        writer.writeheader()
        writer.writerows(summary_rows)

    serializable_rows = [
        {**row, "모집인원": int(row["모집인원"])}
        for row in rows
    ]
    WEB_DATA_JS.write_text(
        "window.모집공고Data = "
        + json.dumps(serializable_rows, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )

    print(f"원본 공고: {len(rows)}건")
    print(f"분야별 CSV: {len(grouped)}개 ({SPLIT_DIR.name})")
    print(f"집계표: {SUMMARY_CSV.name}")
    print(f"웹 데이터: {WEB_DATA_JS.name}")


if __name__ == "__main__":
    main()
