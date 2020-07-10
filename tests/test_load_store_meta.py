import unittest as ut
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID
from uri import URI

from data.common import ImageMetadata
from data.filexp import load_meta, write_meta


class TestLoadStore(ut.TestCase):
    def setUp(self) -> None:
        self.test_dir = TemporaryDirectory()
        self.test_path = Path(self.test_dir.name)

    def tearDown(self) -> None:
        self.test_dir.cleanup()

    def test_load_missing(self):
        blank_meta = load_meta(self.test_path)

        # Verify that the metadata is blank, apart from ID and file name
        self.assertIsNotNone(blank_meta.img_id)
        self.assertIsNotNone(blank_meta.file)
        self.assertIsNone(blank_meta.author)
        self.assertIsNone(blank_meta.universe)
        self.assertIsNone(blank_meta.characters)
        self.assertIsNone(blank_meta.tags)

    def test_load_actual(self):
        image_uri = URI(self.test_path / "test.png")
        with (self.test_path / "test.xml").open('w') as f:
            f.write("<image id=\"97ed6183-73a0-46ea-b51d-0721b0fbd357\" file=\"" + str(image_uri) + "\">" +
                    "<author>a</author><universe>u</universe>" +
                    "<characters><character>x</character><character>y</character></characters>" +
                    "<tags><tag>f</tag><tag>a</tag></tags></image>")

        self.assertEqual(ImageMetadata(UUID('97ed6183-73a0-46ea-b51d-0721b0fbd357'),
                                       image_uri,
                                       "a",
                                       "u",
                                       ["x", "y"],
                                       ["f", "a"]),
                         load_meta(Path(self.test_dir.name) / "test.png"))

    def test_parse_error(self):
        with (self.test_path / "invalid.xml").open('w') as f:
            # Write an invalid XML file
            f.write("<image id=\"kler\" filename=\"kls\">")

        loaded_meta = load_meta(Path(self.test_dir.name) / "invalid.png")

        # Verify that the parse error has been masked as blank metadata
        self.assertIsNotNone(loaded_meta.img_id)
        self.assertIsNotNone(loaded_meta.file)
        self.assertIsNone(loaded_meta.author)
        self.assertIsNone(loaded_meta.universe)
        self.assertIsNone(loaded_meta.characters)
        self.assertIsNone(loaded_meta.tags)

    def test_read_error(self):
        # Create an unreadable file
        (self.test_path / 'inaccessible.xml').touch(mode=0o0222)

        loaded_meta = load_meta(Path(self.test_dir.name) / "inaccessible.png")

        # Verify that the IO error has been masked as blank metadata
        self.assertIsNotNone(loaded_meta.img_id)
        self.assertIsNotNone(loaded_meta.file)
        self.assertIsNone(loaded_meta.author)
        self.assertIsNone(loaded_meta.universe)
        self.assertIsNone(loaded_meta.characters)
        self.assertIsNone(loaded_meta.tags)

    def test_store(self):
        image_uri = URI(self.test_path / "test.png")
        write_meta(ImageMetadata(UUID('97ed6183-73a0-46ea-b51d-0721b0fbd357'),
                                 image_uri,
                                 "a",
                                 "u",
                                 ["x", "y"],
                                 ["f", "a"]),
                   Path(self.test_dir.name) / "test.png")

        with (self.test_path / "test.xml") as f:
            result = f.read_text()

        self.assertEqual("<image id=\"97ed6183-73a0-46ea-b51d-0721b0fbd357\" file=\"" + str(image_uri) + "\">" +
                         "<author>a</author><universe>u</universe>" +
                         "<characters><character>x</character><character>y</character></characters>" +
                         "<tags><tag>f</tag><tag>a</tag></tags></image>",
                         result)

    def test_legacy_load(self):
        image_uri = URI(self.test_path / "test.png")
        with (self.test_path / "test.xml").open('w') as f:
            f.write("<image id=\"97ed6183-73a0-46ea-b51d-0721b0fbd357\" filename=\"test.png\"></image>")

        loaded = load_meta(Path(image_uri.path))
        self.assertEqual(ImageMetadata(UUID('97ed6183-73a0-46ea-b51d-0721b0fbd357'), image_uri, None, None, None, None),
                         loaded)
