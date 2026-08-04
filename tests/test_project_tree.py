from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.project_tree import iter_project_files


class ProjectTreeTests(unittest.TestCase):
    def test_default_traversal_excludes_pytest_cache(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "current.md").write_text("current\n", encoding="utf-8")
            (root / ".pytest_cache").mkdir()
            (root / ".pytest_cache" / "README.md").write_text(
                "generated\n", encoding="utf-8"
            )

            observed = {
                path.relative_to(root).as_posix()
                for path in iter_project_files(root, "*.md")
            }

        self.assertEqual(observed, {"docs/current.md"})


if __name__ == "__main__":
    unittest.main()
