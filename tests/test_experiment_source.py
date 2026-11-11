import tempfile
import unittest
from pathlib import Path

from tools.experiments.source_optimization_analysis import strip_nonsemantic_lines


class SourceOptimizationTests(unittest.TestCase):
    def test_strips_only_full_line_comments_and_blank_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            target = Path(directory) / "target"
            source.write_text("#!/bin/sh\n# comment\nvalue='# keep'\n\n")
            strip_nonsemantic_lines(source, target)
            self.assertEqual(target.read_text(), "#!/bin/sh\nvalue='# keep'\n")


if __name__ == "__main__":
    unittest.main()
