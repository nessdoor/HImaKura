import unittest as ut
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from common import ImageMetadata
from filexp import load_meta, write_meta


class TestLoadStore(ut.TestCase):
    def setUp(self) -> None:
        self.test_dir = TemporaryDirectory()

    def tearDown(self) -> None:
        self.test_dir.cleanup()

    def test_load_missing(self):
        blank_meta = load_meta(Path(self.test_dir.name))

        # Verify that the metadata is blank, apart from ID and file name
        self.assertIsNotNone(blank_meta.img_id)
        self.assertIsNotNone(blank_meta.filename)
        self.assertIsNone(blank_meta.author)
        self.assertIsNone(blank_meta.universe)
        self.assertIsNone(blank_meta.characters)
        self.assertIsNone(blank_meta.tags)

    def test_load_actual(self):
        with (Path(self.test_dir.name) / "test.xml").open('w') as f:
            f.write("<image id=\"97ed6183-73a0-46ea-b51d-0721b0fbd357\" filename=\"test.png\">" +
                    "<author>a</author><universe>u</universe>" +
                    "<characters><character>x</character><character>y</character></characters>" +
                    "<tags><tag>f</tag><tag>a</tag></tags></image>")

        self.assertEqual(ImageMetadata(UUID('97ed6183-73a0-46ea-b51d-0721b0fbd357'),
                                       "test.png",
                                       "a",
                                       "u",
                                       ["x", "y"],
                                       ["f", "a"]),
                         load_meta(Path(self.test_dir.name) / "test.png"))

    def test_store(self):
        write_meta(ImageMetadata(UUID('97ed6183-73a0-46ea-b51d-0721b0fbd357'),
                                 "test.png",
                                 "a",
                                 "u",
                                 ["x", "y"],
                                 ["f", "a"]),
                   Path(self.test_dir.name) / "test.png")

        with (Path(self.test_dir.name) / "test.xml") as f:
            result = f.read_text()

        self.assertEqual("<image id=\"97ed6183-73a0-46ea-b51d-0721b0fbd357\" filename=\"test.png\">" +
                         "<author>a</author><universe>u</universe>" +
                         "<characters><character>x</character><character>y</character></characters>" +
                         "<tags><tag>f</tag><tag>a</tag></tags></image>",
                         result)
