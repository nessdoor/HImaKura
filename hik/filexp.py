from mimetypes import guess_type
from pathlib import Path
from typing import Tuple, List, Optional


class Carousel:
    """
    A slider that moves over a collection of (eventually tagged) images contained in a directory.

    By using the two methods `prev()` and `next()`, one can slide over the collection while being provided with
    `(image path, metadata path)` tuples via return values.
    If the current image doesn't have a readable accompanying XML metadata file, `None` is returned.
    Trying to slide out of the collection's boundaries causes a `StopIteration` exception to be raised.
    This object contains state information about the images' path. Any insertion or deletion of images into the base
    directory after this object gets created will be ignored or will cause the carousel to return invalid paths.
    """

    _base_path: Path
    _image_files: List[Path]
    _current: int
    _length: int

    def __init__(self, directory: Path):
        """
        Instantiates a new slider over the collection of images under the given path.

        :param directory: a directory path under which the slider will look-up images
        :raise FileNotFoundError: when no directory exists at the specified path
        :raise NotADirectoryException: when the provided path points to a file that is not a directory
        """

        if not directory.exists():
            raise FileNotFoundError

        if not directory.is_dir():
            raise NotADirectoryError

        self._base_path = directory
        # List the directory's contents and filter out any non-image file
        self._image_files = [img for img in directory.iterdir()
                             if img.is_file() and guess_type(img)[0].partition('/')[0] == 'image']
        # The first step should bring us at position 0
        self._current = -1
        self._length = len(self._image_files)

    def _get_metadata_path(self, image: Path) -> Optional[Path]:
        sibling_xml = self._base_path / (image.stem + '.xml')
        return sibling_xml if sibling_xml.exists() else None

    def prev(self) -> Tuple[Path, Path]:
        """Get the previous image/metadata pair."""

        # The initial index is negative, and we shouldn't go back to it, hence the `<=`.
        if self._current <= 0:
            raise StopIteration

        self._current -= 1
        image_path = self._image_files[self._current]
        return image_path, self._get_metadata_path(image_path)

    def next(self) -> Tuple[Path, Path]:
        """Get the next image/metadata pair."""

        if self._current == self._length - 1:
            raise StopIteration

        self._current += 1
        image_path = self._image_files[self._current]
        return image_path, self._get_metadata_path(image_path)
