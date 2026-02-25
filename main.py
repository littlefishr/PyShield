#!/usr/bin/env python3
"""CLI 入口，用于创建/检查文件完整性基线并用 rich 美化输出。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.fim import FileIntegrityMonitor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="File Integrity Monitor CLI")
    parser.add_argument(
        "--path",
        "-p",
        default=".",
        help="Directory to monitor (default: current directory)",
    )
    parser.add_argument(
        "--action",
        "-a",
        choices=["baseline", "check"],
        default="check",
        help="Action to perform: 'baseline' or 'check' (default: check)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="baseline.json",
        help="Baseline file path (default: baseline.json)",
    )

    args = parser.parse_args(argv)

    console = Console()

    root = Path(args.path)
    out = Path(args.output)

    try:
        if args.action == "baseline":
            FileIntegrityMonitor.create_baseline(root, out)

            # 读取基线文件以统计扫描到的文件数（若无法读取则显示 0）
            try:
                baseline_data = json.loads(out.read_text()) if out.exists() else {}
                scanned = len(baseline_data)
            except Exception:
                scanned = 0

            table = Table(title="Baseline Created", show_header=True)
            table.add_column("Scanned Files", justify="right")
            table.add_row(str(scanned))
            console.print(Panel(table, style="green"))
            return 0

        # check
        result = FileIntegrityMonitor.check_integrity(root, out)

        modified = result.get("modified", [])
        added = result.get("added", [])
        deleted = result.get("deleted", [])

        if modified or added or deleted:
            # 有变动，逐类显示红色高亮
            console.print(Panel(Text("Integrity issues detected", style="bold red")))

            def print_list(title: str, items: list[str], style: str = "red") -> None:
                if not items:
                    return
                tbl = Table(title=title)
                tbl.add_column("Path")
                for p in items:
                    tbl.add_row(Text(p, style=style))
                console.print(tbl)

            print_list("Modified", sorted(modified), "red")
            print_list("Added", sorted(added), "red")
            print_list("Deleted", sorted(deleted), "red")
            return 2
        else:
            console.print(Panel(Text("System Integrity Verified", style="bold green")))
            return 0

    except Exception as exc:  # 捕获所有异常，避免程序崩溃
        console.print(Panel(Text(str(exc), style="bold red"), title="Error"))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


# Test trigger for security review