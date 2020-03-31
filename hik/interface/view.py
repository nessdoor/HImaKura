from pathlib import Path
from typing import Optional

from gi.repository.GdkPixbuf import Pixbuf

from common import ImageMetadata
from filexp import Carousel, load_bundle, write_meta


class View:
    """
    The class for objects representing the state of the current view.

    It wraps the inner carousel and retrieves images and metadata objects, exposing them to the frontend.
    The image is exposed as an untouched GDK pixbuf.
    """

    _carousel: Carousel
    _current_image: Pixbuf
    _image_path: Path
    _current_meta: ImageMetadata
    _meta_path: Path

    def __init__(self, context_dir: Path):
        """Instantiate a new view over the valid contents at the specified path."""

        self._carousel = Carousel(context_dir)

    def prev(self):
        """
        Retrieve the previous image and its metadata.

        :raise StopIteration: when the carousel has reached the start of the collection
        """

        self._image_path, self._meta_path = self._carousel.prev()
        self._current_image, self._current_meta = load_bundle(self._image_path, self._meta_path)

    def next(self):
        """Retrieve the next image and its metadata.

        :raise StopIteration: when the carousel has reached the end of the collection
        """

        self._image_path, self._meta_path = self._carousel.next()
        self._current_image, self._current_meta = load_bundle(self._image_path, self._meta_path)

    def get_image(self) -> Pixbuf:
        return self._current_image.copy()

    def set_author(self, author: str):
        o = self._current_meta
        if len(author) == 0:
            author = None

        self._current_meta = ImageMetadata(o.img_id, o.filename, author, o.universe, o.characters, o.tags)

    def get_author(self) -> Optional[str]:
        return self._current_meta.author

    def set_universe(self, universe: str):
        o = self._current_meta
        if len(universe) == 0:
            universe = None

        self._current_meta = ImageMetadata(o.img_id, o.filename, o.author, universe, o.characters, o.tags)

    def get_universe(self) -> Optional[str]:
        return self._current_meta.universe

    def set_characters(self, characters: str):
        o = self._current_meta
        if len(characters) == 0:
            new_chars = None
        else:
            new_chars = characters.split(',')

        self._current_meta = ImageMetadata(o.img_id, o.filename, o.author, o.universe, new_chars, o.tags)

    def get_characters(self) -> Optional[str]:
        return ', '.join(self._current_meta.characters) if self._current_meta.characters is not None else None

    def set_tags(self, tags: str):
        o = self._current_meta
        if len(tags) == 0:
            new_tags = None
        else:
            new_tags = tags.split(',')

        self._current_meta = ImageMetadata(o.img_id, o.filename, o.author, o.universe, o.characters, new_tags)

    def get_tags(self) -> Optional[str]:
        return ', '.join(self._current_meta.tags) if self._current_meta.tags is not None else None

    def write(self):
        """
        Write out the new metadata.

        :raise OSError
        """

        if self._meta_path is None:
            write_meta(self._current_meta, self._image_path.parent / (self._image_path.stem + '.xml'))
        else:
            write_meta(self._current_meta, self._meta_path)
