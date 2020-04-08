from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory
from unittest import TestCase
from uuid import UUID

from common import ImageMetadata
from filexp import write_meta, load_meta
from interface.view import View


class TestView(TestCase):
    def setUp(self) -> None:
        self.test_dir = TemporaryDirectory()

        # We happen to have an image in this repo, so let's use it
        copyfile(Path(__file__).parent.parent / "screenshots" / "main_screen.png",
                 Path(self.test_dir.name) / "01.png")
        copyfile(Path(__file__).parent.parent / "screenshots" / "main_screen.png",
                 Path(self.test_dir.name) / "02.png")

    def tearDown(self) -> None:
        self.test_dir.cleanup()

    def test_carousel_behaviour(self):
        specimen = View(Path(self.test_dir.name))

        # Setup callback detection system
        class Flag:
            def __init__(self):
                self.flag = None

            def set_flag(self, val):
                self.flag = val

        prev_flag = Flag()
        next_flag = Flag()

        specimen.set_prev_callback(lambda v: prev_flag.set_flag(v.has_prev()))
        specimen.set_next_callback(lambda v: next_flag.set_flag(v.has_next()))

        # Verify correct forward-iteration and callback effect
        specimen.load_next()
        self.assertIsNone(prev_flag.flag)
        self.assertTrue(next_flag.flag)
        specimen.load_next()
        self.assertFalse(next_flag.flag)

        # Verify StopIteration behaviour and callback absence
        next_flag.flag = None
        self.assertRaises(StopIteration, specimen.load_next)
        self.assertIsNone(prev_flag.flag)
        self.assertIsNone(next_flag.flag)

        # Do exactly the same for reverse-iteration
        specimen.load_prev()
        self.assertFalse(prev_flag.flag)
        self.assertIsNone(next_flag.flag)

        prev_flag.flag = None
        self.assertRaises(StopIteration, specimen.load_prev)
        self.assertIsNone(prev_flag.flag)
        self.assertIsNone(next_flag.flag)

    @staticmethod
    def meta_extractor(v: View) -> ImageMetadata:
        characters = v.get_characters()
        characters = characters.split(', ') if characters is not None else None

        tags = v.get_tags()
        tags = tags.split(', ') if tags is not None else None

        return ImageMetadata(v.image_id, v.filename, v.get_author(), v.get_universe(), characters, tags)

    def test_metadata_read(self):
        # Write some metadata for one of the images
        meta1 = ImageMetadata(img_id=UUID('f32ed6ad-1162-4ea6-b243-1e6c91fb7eda'),
                              filename='01.png',
                              author="a",
                              universe="p",
                              characters=["x", "y"],
                              tags=["t", "f"])
        write_meta(meta1, (Path(self.test_dir.name) / '01.png'))

        specimen = View(Path(self.test_dir.name))

        # Collect metadata from the specimen
        results = dict()
        for _ in range(0, 2):
            specimen.load_next()
            results[specimen.filename] = TestView.meta_extractor(specimen)

        self.assertEqual(meta1, results["01.png"])
        self.assertEqual(ImageMetadata(results["02.png"].img_id, "02.png", None, None, None, None), results["02.png"])

    def test_metadata_update(self):
        target_filename = '02.png'
        specimen = View(Path(self.test_dir.name))

        # Scan until we find our target
        specimen.load_next()
        while specimen.filename != target_filename:
            specimen.load_next()

        # Verify that no metadata is present
        self.assertIsNone(specimen.get_tags())

        # Set metadata and check coherence
        specimen.set_author(":DD")
        specimen.set_universe("u")
        specimen.set_characters("3, f,p")
        specimen.set_tags("fa,s jo, l")
        specimen.write()

        self.assertEqual(
            ImageMetadata(specimen.image_id, target_filename, ":DD", "u", ["3", "f", "p"], ["fa", "s jo", "l"]),
            load_meta(Path(self.test_dir.name) / target_filename))