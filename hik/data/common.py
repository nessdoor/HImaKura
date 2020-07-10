from typing import NamedTuple, Optional, Iterable
from uuid import UUID
from uri import URI


class ImageMetadata(NamedTuple):
    """
    An immutable object containing image metadata.

    img_id - a UUID identifying the image
    file - URI of the described image
    author - the image's author (optional)
    universe - name of the universe to which the characters or scenery belong (optional)
    characters - a list of the characters involved (optional)
    tags - a list of tags associated with the image (optional)
    """

    img_id: UUID
    file: URI
    author: Optional[str]
    universe: Optional[str]
    characters: Optional[Iterable[str]]
    tags: Optional[Iterable[str]]
