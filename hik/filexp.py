from mimetypes import guess_type
from pathlib import Path
from typing import Tuple, List, Optional
from uuid import uuid4

from common import ImageMetadata

import gi

from xmngr import parse_xml, generate_xml

gi.require_version('GdkPixbuf', '2.0')
from gi.repository.GdkPixbuf import Pixbuf


class Carousel:
    """
    A slider that moves over a collection of (eventually tagged) images contained in a directory.

    By using the two methods `prev()` and `next()`, one can slide over the collection while being provided with
    `(image path, metadata path)` tuples via return values.
    If the current image doesn't have a readable accompanying XML metadata file, `None` is returned.
    Trying to slide out of the collection's boundaries causes a `StopIteration` exception to be raised.
    """

    _base_path: Path
    _image_files: List[Path]
    _current: int

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

    def _get_metadata_path(self, image: Path) -> Optional[Path]:
        sibling_xml = self._base_path / (image.stem + '.xml')
        return sibling_xml if sibling_xml.exists() else None

    def has_prev(self) -> bool:
        """
        Tell if the carousel can presently go back to a previous image.

        Be aware that this method does not check if the previous image still exists.
        """

        return self._current > 0

    def prev(self) -> Tuple[Path, Path]:
        """Get the previous image/metadata pair."""

        # The initial index is negative, and we shouldn't go back to it, hence the `<=`.
        if not self.has_prev():
            raise StopIteration

        self._current -= 1
        image_path = self._image_files[self._current]
        if image_path.exists():
            return image_path, self._get_metadata_path(image_path)
        else:
            del self._image_files[self._current]
            return self.prev()

    def has_next(self) -> bool:
        """
        Tell if the carousel can presently move forward to the next image.

        Be aware that this method does not check if the next image still exists.
        """

        return self._current < len(self._image_files) - 1

    def next(self) -> Tuple[Path, Path]:
        """Get the next image/metadata pair."""

        if not self.has_next():
            raise StopIteration

        image_path = self._image_files[self._current + 1]
        if image_path.exists():
            self._current += 1
            return image_path, self._get_metadata_path(image_path)
        else:
            del self._image_files[self._current + 1]
            return self.next()


def load_bundle(img_file: Path, meta_file: Optional[Path]) -> Tuple[Pixbuf, ImageMetadata]:
    """Load a pixbuf/metadata tuple from a couple of paths pointing to an image file and its eventual metadata"""

    image = Pixbuf.new_from_file(str(img_file))

    if meta_file is not None:
        with meta_file.open() as mf:
            try:
                metadata = parse_xml(mf.read())
            except OSError:
                metadata = ImageMetadata(uuid4(), img_file.name, None, None, None, None)
    else:
        metadata = ImageMetadata(uuid4(), img_file.name, None, None, None, None)

    return image, metadata


def write_meta(metadata: ImageMetadata, dest: Path):
    with dest.open('w') as o:
        o.write(generate_xml(*metadata))
