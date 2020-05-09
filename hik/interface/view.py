import stringprep
from pathlib import Path
from typing import Optional, Iterable, Callable
from uuid import UUID

from gi.repository.GdkPixbuf import Pixbuf

from data.common import ImageMetadata
from data.filexp import Carousel, write_meta, load_meta


def remove_control_and_redundant_space(s: str) -> str:
    """Substitute multiple concatenated control and space characters into single whitespace."""

    res = ''
    for ch in s:
        # Convert Unicode control and space characters into simple whitespaces
        ss = ch if not stringprep.in_table_c11_c12(ch) and not stringprep.in_table_c21_c22(ch) else ' '
        res += ss

    # Remove redundant spaces
    return ' '.join(res.split())


class View:
    """
    The state of the current view.

    It wraps the inner carousel and retrieves images and metadata objects, exposing them to the frontend.
    Images are exposed as unmodified GDK pixbufs.
    """

    _carousel: Carousel
    _current_image: Pixbuf
    _image_path: Path
    _prev_callback: Optional[Callable]
    _next_callback: Optional[Callable]

    # Image metadata
    _id: UUID
    _filename: str
    author: Optional[str]
    universe: Optional[str]
    characters: Optional[Iterable[str]]
    tags: Optional[Iterable[str]]

    def __init__(self, context_dir: Path):
        """
        Instantiate a new view over the image/metadata file pairs at the specified path.

        The new view will have most of its data uninitialized, since to load them means to start scanning the contents.
        Therefore, before attempting to retrieve any data, call the `load_next()` method.

        :arg context_dir: path to the directory under which all operations will be performed
        :raise FileNotFoundError: when the path points to an invalid location
        :raise NotADirectoryException: when the path point to a file that is not a directory
        """

        self._carousel = Carousel(context_dir)
        self._prev_callback = None
        self._next_callback = None

    def _update_meta(self, meta: ImageMetadata) -> None:
        self._id = meta.img_id
        self._filename = meta.filename
        self.author = meta.author
        self.universe = meta.universe
        self.characters = meta.characters
        self.tags = meta.tags

    def set_prev_callback(self, callback: Callable) -> None:
        """Set the callback object to call after each `prev` invocation.

        The callable object must accept a single argument representing this View object. Any returned value will be
        ignored.
        :arg callback: the callable object to be used as a callback
        """

        self._prev_callback = callback

    def set_next_callback(self, callback: Callable) -> None:
        """
        Set the callback object to call after each `next` invocation.

        The callable object must accept a single argument representing this View object. Any returned value will be
        ignored.
        :arg callback: the callable object to be used as a callback
        """

        self._next_callback = callback

    def has_image_data(self) -> bool:
        """Tell if the current view contains valid image data."""

        return hasattr(self, '_current_image')

    def has_prev(self) -> bool:
        """Check whether there is a previous image."""

        return self._carousel.has_prev()

    def has_next(self) -> bool:
        """Check whether there is a next image."""

        return self._carousel.has_next()

    def load_prev(self) -> None:
        """
        Retrieve the previous image and its metadata.

        If a callback function was set, it will be called after having successfully loaded all the data.
        :raise StopIteration: when the start of the collection has already been reached
        """

        self._image_path = self._carousel.prev()
        self._current_image = Pixbuf.new_from_file(str(self._image_path))
        self._update_meta(load_meta(self._image_path))

        if self._prev_callback is not None:
            self._prev_callback(self)

    def load_next(self) -> None:
        """Retrieve the next image and its metadata.

        If a callback function was set, it will be called after having successfully loaded all the data.
        :raise StopIteration: when the end of the collection has already been reached
        """

        self._image_path = self._carousel.next()
        self._current_image = Pixbuf.new_from_file(str(self._image_path))
        self._update_meta(load_meta(self._image_path))

        if self._next_callback is not None:
            self._next_callback(self)

    @property
    def image_id(self) -> UUID:
        return self._id

    @property
    def filename(self) -> str:
        return self._filename

    def get_image_contents(self) -> Optional[Pixbuf]:
        """
        Return the image as a pixbuf copy.

        :return: a pixbuf containing the image, or None if no image has been loaded
        """

        if self.has_image_data():
            return self._current_image.copy()
        else:
            return None

    def set_author(self, author: str) -> None:
        if len(author) == 0:
            author = None
        else:
            author = remove_control_and_redundant_space(author)

        self.author = author

    def get_author(self) -> Optional[str]:
        return self.author

    def set_universe(self, universe: str) -> None:
        if len(universe) == 0:
            universe = None
        else:
            universe = remove_control_and_redundant_space(universe)

        self.universe = universe

    def get_universe(self) -> Optional[str]:
        return self.universe

    def set_characters(self, characters: str) -> None:
        """Take a comma-separated list of characters in input and use it to update the metadata."""

        if len(characters) == 0:
            new_chars = None
        else:
            new_chars = remove_control_and_redundant_space(characters)
            new_chars = new_chars.split(',')
            new_chars = [c.strip() for c in new_chars]

        self.characters = new_chars

    def get_characters(self) -> Optional[str]:
        """Return the characters in a comma-separated list, or None if no character metadata is present."""

        if self.characters is not None:
            return ', '.join(self.characters)
        else:
            return None

    def set_tags(self, tags: str) -> None:
        """Take a comma-separated list of tags in input and use it to update the metadata."""

        if len(tags) == 0:
            new_tags = None
        else:
            new_tags = remove_control_and_redundant_space(tags)
            new_tags = new_tags.split(',')
            new_tags = [t.strip() for t in new_tags]

        self.tags = new_tags

    def get_tags(self) -> Optional[str]:
        """Return the image tags in a comma-separated list, or None if no tag metadata is present."""

        if self.tags is not None:
            return ', '.join(self.tags)
        else:
            return None

    def write(self) -> None:
        """
        Persist the updated metadata.

        :raise OSError: when the metadata file couldn't be opened
        """

        meta_obj = ImageMetadata(self._id, self._filename, self.author, self.universe, self.characters, self.tags)
        write_meta(meta_obj, self._image_path)
