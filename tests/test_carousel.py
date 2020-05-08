import os
import unittest as ut
from pathlib import Path
from tempfile import TemporaryDirectory

from data.filexp import Carousel


class TestCarouselConstruction(ut.TestCase):
    def setUp(self) -> None:
        self.test_dir = TemporaryDirectory()

    def tearDown(self) -> None:
        self.test_dir.cleanup()

    def test_nonexistent_directory(self):
        with self.assertRaises(FileNotFoundError):
            Carousel(Path(Path(self.test_dir.name) / 'nonexistent'))

    def test_not_a_dir(self):
        empty_file = open(Path(self.test_dir.name) / 'empty', 'a')

        with self.assertRaises(NotADirectoryError):
            Carousel(Path(empty_file.name))

        empty_file.close()

    def test_with_images(self):
        filenames = ["01.png", "01.xml", "03.jpg", "04.pdf", "foo"]
        for name in filenames:
            (Path(self.test_dir.name) / name).touch()

        specimen = Carousel(Path(self.test_dir.name))

        # Verify that the image files have been picked-up by the object
        self.assertEqual({"01.png", "03.jpg"}, set(map(lambda p: p.name, specimen._image_files)))

    def test_filter(self):
        filenames = ["included.png", "excluded.jpg"]
        for name in filenames:
            (Path(self.test_dir.name) / name).touch()

        specimen = Carousel(Path(self.test_dir.name), lambda path: path.stem == 'included')

        self.assertEqual([Path(self.test_dir.name) / "included.png"], specimen._image_files)


class TestCarouselBehaviour(ut.TestCase):
    def setUp(self) -> None:
        self.test_dir = TemporaryDirectory()

    def tearDown(self) -> None:
        self.test_dir.cleanup()

    def test_iteration_empty(self):
        specimen = Carousel(Path(self.test_dir.name))

        self.assertRaises(StopIteration, lambda: specimen.prev())
        self.assertRaises(StopIteration, lambda: specimen.next())

    def test_regular_iteration(self):
        filenames = ["01.png", "01.xml", "03.jpg"]
        fobs = []
        for name in filenames:
            fobs.append(open(Path(self.test_dir.name) / name, 'a'))
        # Valid paths that should be produced by an iteration over the entire test directory
        expected_paths = {Path(self.test_dir.name) / "01.png",
                          Path(self.test_dir.name) / "03.jpg"}

        specimen = Carousel(Path(self.test_dir.name))

        # Perform forward iteration until StopIteration
        # This movement must uncover all the images
        full_scan_results = set()
        for _ in range(0, len(expected_paths)):
            self.assertTrue(specimen.has_next())
            full_scan_results.add(specimen.next())

        self.assertFalse(specimen.has_next())
        self.assertRaises(StopIteration, lambda: specimen.next())
        self.assertEqual(expected_paths, full_scan_results)

        # Perform reverse iteration until StopIteration
        # This movement must go back to the first item, not returning the current one again
        reverse_scan_results = set()
        self.assertTrue(specimen.has_prev())
        reverse_scan_results.add(specimen.prev())

        self.assertFalse(specimen.has_prev())
        self.assertRaises(StopIteration, lambda: specimen.prev())
        self.assertTrue(len(reverse_scan_results) > 0)
        self.assertTrue(expected_paths > reverse_scan_results)

        # Perform the movement once again and move forward
        # This movement must move again towards the last item, without returning the current one again
        forward_scan_results = set()
        self.assertTrue(specimen.has_next())
        forward_scan_results.add(specimen.next())

        self.assertFalse(specimen.has_next())
        self.assertRaises(StopIteration, lambda: specimen.next())
        self.assertTrue(len(forward_scan_results) > 0)
        self.assertTrue(expected_paths > forward_scan_results)
        self.assertNotEqual(reverse_scan_results, forward_scan_results)

        for file in fobs:
            file.close()

    def test_file_deletion_after_creation(self):
        test_dir_path = Path(self.test_dir.name)
        first = "first.png"
        fo = open(test_dir_path / first, 'a')
        second = "second.png"
        so = open(test_dir_path / second, 'a')
        third = "third.png"
        to = open(test_dir_path / third, 'a')
        fourth = "fourth.png"
        yo = open(test_dir_path / fourth, 'a')

        specimen = Carousel(test_dir_path)
        fo.close()
        os.remove(test_dir_path / first)
        results = set()
        # Perform a full scan
        for _ in range(0, 3):
            results.add(specimen.next())

        # 'First' shouldn't be among the results
        self.assertEqual({test_dir_path / second, test_dir_path / third, test_dir_path / fourth}, results)
        self.assertFalse(specimen.has_next())
        self.assertRaises(StopIteration, lambda: specimen.next())

        so.close()
        os.remove(test_dir_path / second)
        to.close()
        os.remove(test_dir_path / third)

        # Iteration should now jump straight at the fourth element
        self.assertTrue(specimen.has_prev())
        self.assertEqual(test_dir_path / fourth, specimen.prev())
        self.assertFalse(specimen.has_prev())
        self.assertRaises(StopIteration, lambda: specimen.prev())

        yo.close()
        os.remove(test_dir_path / fourth)

        # Carousel should now be stuck
        self.assertFalse(specimen.has_next())
        self.assertRaises(StopIteration, lambda: specimen.next())
        self.assertFalse(specimen.has_prev())
        self.assertRaises(StopIteration, lambda: specimen.prev())
