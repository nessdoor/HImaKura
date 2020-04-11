from mimetypes import guess_type
from pathlib import Path
from typing import List
from uuid import uuid4

from common import ImageMetadata
from xmngr import parse_xml, generate_xml


class Carousel:
    """
    A slider that moves over a collection of (eventually tagged) images contained in a directory.

    By using the two methods `prev()` and `next()`, one can slide over the collection while being provided with new
    image paths.
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
                             if img.is_file()
                             and guess_type(img)[0] is not None
                             and guess_type(img)[0].partition('/')[0] == 'image']
        # The first step should bring us at position 0
        self._current = -1

    def has_prev(self) -> bool:
        """
        Tell if the carousel can presently go back to a previous image.

        If there was an image preceding the current one, but it has been deleted since the instantiation of the object,
        then invoking this method alters the state of the carousel by removing the non-existent image(s) from the
        internal record.
        """

        if self._current > 0:
            precedent = self._current - 1
            if not self._image_files[precedent].exists():
                del self._image_files[precedent]
                self._current -= precedent
                return self.has_prev()

            return True

        return False

    def prev(self) -> Path:
        """
        Get the previous image.

        :return: a Path pointing to the new current image
        :raise StopIteration: when there is no image preceding the current one
        """

        if not self.has_prev():
            raise StopIteration

        self._current -= 1
        return self._image_files[self._current]

    def has_next(self) -> bool:
        """
        Tell if the carousel can presently move forward to the next image.

        If there was an image following the current one, but it has been deleted since the instantiation of the object,
        then invoking this method alters the state of the carousel by removing the non-existent image(s) from the
        internal record.
        """

        if self._current < len(self._image_files) - 1:
            follower = self._current + 1
            if not self._image_files[follower].exists():
                del self._image_files[follower]
                return self.has_next()

            return True

        return False

    def next(self) -> Path:
        """
        Get the next image.

        :return: a Path pointing to the new current image
        :raise StopIteration: when there is no image following the current one
        """

        if not self.has_next():
            raise StopIteration

        self._current += 1
        return self._image_files[self._current]


def _construct_metadata_path(image_path: Path) -> Path:
    return image_path.parent / (image_path.stem + '.xml')


def load_meta(img_file: Path) -> ImageMetadata:
    """
    Load the metadata tuple for a given image file.

    If no metadata file is present, return a blank metadata tuple.

    :arg img_file: a path pointing to a managed image for which we want to load metadata
    :return: the associated metadata as a tuple, or a blank metadata tuple
    """

    meta_file = _construct_metadata_path(img_file)

    if meta_file.exists():
        with meta_file.open() as mf:
            try:
                metadata = parse_xml(mf.read())
            except OSError:
                metadata = ImageMetadata(uuid4(), img_file.name, None, None, None, None)
    else:
        metadata = ImageMetadata(uuid4(), img_file.name, None, None, None, None)

    return metadata


def write_meta(metadata: ImageMetadata, img_file: Path) -> None:
    """
    Write the updated metadata for a given image.
    
    :param metadata: the metadata object to be written out
    :param img_file: the image to which the metadata is associated
    """

    dst = _construct_metadata_path(img_file)
    with dst.open('w') as o:
        o.write(generate_xml(metadata))
