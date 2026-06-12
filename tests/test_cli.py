import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NO_BYTECODE_ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


class CliTests(unittest.TestCase):
    def _cost_data(self):
        return {
            "product": {
                "name": "Test Product",
                "price": 100,
                "category": "消费电子",
            },
            "breakdown": [
                {
                    "dimension": "物料成本(BOM)",
                    "amount": 30,
                    "pct": 30,
                    "min_pct": 20,
                    "max_pct": 35,
                    "confidence": 3,
                    "source": "test baseline",
                }
            ],
            "summary": {
                "total_pct": 100,
                "overall_confidence": 3,
                "hard_data_points": 0,
                "estimated_points": 1,
            },
        }

    def test_generate_md_report_accepts_input_and_output_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "cost.json"
            output_path = tmp_path / "report.md"
            input_path.write_text(json.dumps(self._cost_data(), ensure_ascii=False), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "generate_md_report.py"),
                    str(input_path),
                    str(output_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                env=NO_BYTECODE_ENV,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output_path.exists())
            self.assertIn("Test Product", output_path.read_text(encoding="utf-8"))

    def test_report_generators_accept_utf8_bom_input_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "cost.json"
            md_output = tmp_path / "report.md"
            html_output = tmp_path / "report.html"
            input_path.write_text(json.dumps(self._cost_data(), ensure_ascii=False), encoding="utf-8-sig")

            md_result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "generate_md_report.py"),
                    str(input_path),
                    str(md_output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                env=NO_BYTECODE_ENV,
            )
            html_result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "generate_html_report.py"),
                    str(input_path),
                    str(html_output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                env=NO_BYTECODE_ENV,
            )

            self.assertEqual(md_result.returncode, 0, md_result.stderr)
            self.assertEqual(html_result.returncode, 0, html_result.stderr)
            self.assertTrue(md_output.exists())
            self.assertTrue(html_output.exists())


if __name__ == "__main__":
    unittest.main()
