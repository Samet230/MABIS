import subprocess
import sys
from pathlib import Path
import pytest

from main import BuildCommandLineParser


def test_cli_parser_help():
    """CLI argüman ayrıştırıcısının argümanları doğru tanıdığını test eder."""
    parser = BuildCommandLineParser()

    # register argümanları
    regArgs = parser.parse_args(
        ["register", "--image", "sample.jpg", "--id", "cow_01", "--species", "cattle"]
    )
    assert regArgs.command == "register"
    assert regArgs.id == "cow_01"
    assert regArgs.species == "cattle"

    # identify argümanları
    identArgs = parser.parse_args(
        ["identify", "--image", "query.jpg", "--species", "dog", "--top-k", "3"]
    )
    assert identArgs.command == "identify"
    assert identArgs.species == "dog"
    assert identArgs.top_k == 3

    # split argümanları
    splitArgs = parser.parse_args(["split", "--species", "cat", "--seed", "100"])
    assert splitArgs.command == "split"
    assert splitArgs.seed == 100


def test_cli_execution_help_screen():
    """main.py dosyasının --help ile başarıyla çalıştığını test eder."""
    result = subprocess.run(
        [sys.executable, "main.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "ZooID" in result.stdout
