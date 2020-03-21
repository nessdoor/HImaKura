import os
import unittest as ut
from pathlib import Path
from tempfile import TemporaryDirectory

from filexp import Carousel


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
        filenames = ["01.png", "01.xml", "03.jpg", "04.pdf"]
        fobs = []
        for name in filenames:
            fobs.append(open(Path(self.test_dir.name) / name, 'a'))

        specimen = Carousel(Path(self.test_dir.name))
        # Verify the correctness of the base path
        self.assertEqual(Path(self.test_dir.name), specimen._base_path)
        # Verify that the image files have been picked-up by the object
        self.assertEqual({"01.png", "03.jpg"}, set(map(lambda p: p.name, specimen._image_files)))

        for file in fobs:
            file.close()


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
        # Valid tuples that should be produced by an iteration over the entire test directory
        expected_tuples = {(Path(self.test_dir.name) / "01.png", Path(self.test_dir.name) / "01.xml"),
                           (Path(self.test_dir.name) / "03.jpg", None)}

        specimen = Carousel(Path(self.test_dir.name))

        # Perform forward iteration until StopIteration
        # This movement must uncover all the images
        full_scan_results = set()
        for _ in range(0, len(expected_tuples)):
            full_scan_results.add(specimen.next())

        self.assertRaises(StopIteration, lambda: specimen.next())
        self.assertEqual(expected_tuples, full_scan_results)

        # Perform reverse iteration until StopIteration
        # This movement must go back to the first item, not returning the current one again
        reverse_scan_results = set()
        reverse_scan_results.add(specimen.prev())

        self.assertRaises(StopIteration, lambda: specimen.prev())
        self.assertTrue(len(reverse_scan_results) > 0)
        self.assertTrue(expected_tuples > reverse_scan_results)

        # Perform the movement once again and move forward
        # This movement must move again towards the last item, without returning the current one again
        forward_scan_results = set()
        forward_scan_results.add(specimen.next())

        self.assertRaises(StopIteration, lambda: specimen.next())
        self.assertTrue(len(forward_scan_results) > 0)
        self.assertTrue(expected_tuples > forward_scan_results)
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

        specimen = Carousel(test_dir_path)
        fo.close()
        os.remove(test_dir_path / first)
        results = set()
        for _ in range(0, 2):
            results.add(specimen.next())

        self.assertEqual({(test_dir_path / second, None), (test_dir_path / third, None)}, results)
        self.assertRaises(StopIteration, lambda: specimen.next())

        so.close()
        os.remove(test_dir_path / second)
        self.assertEqual((test_dir_path / third, None), specimen.prev())
        self.assertRaises(StopIteration, lambda: specimen.prev())

        to.close()
        os.remove(test_dir_path / third)
        self.assertRaises(StopIteration, lambda: specimen.next())
        self.assertRaises(StopIteration, lambda: specimen.prev())
