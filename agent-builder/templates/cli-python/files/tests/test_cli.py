import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from __PKG_NAME__.cli import main  # noqa: E402


def run_cli(*args: str) -> tuple[int, str]:
    out = io.StringIO()
    with redirect_stdout(out):
        code = main(list(args))
    return code, out.getvalue()


class CliTests(unittest.TestCase):
    def test_hello(self) -> None:
        self.assertEqual(run_cli("hello", "Ada"), (0, "Hello, Ada!\n"))

    def test_hello_json_shout(self) -> None:
        code, out = run_cli("--json", "hello", "ada", "--shout")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {"message": "HELLO, ADA!"})

    def test_scan_counts_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.txt").write_text("hi")
            Path(tmp, "b.txt").write_text("there")
            Path(tmp, "c.py").write_text("x = 1")
            code, out = run_cli("--json", "scan", tmp)
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["files"], 3)
        self.assertEqual(data["by_extension"], {".txt": 2, ".py": 1})

    def test_scan_missing_folder(self) -> None:
        code, _ = run_cli("scan", "/definitely/not/here")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
