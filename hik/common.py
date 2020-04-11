from typing import NamedTuple, Optional, Iterable
from uuid import UUID


class ImageMetadata(NamedTuple):
    """
    An immutable object containing image metadata.

    img_id - a UUID identifying the image
    filename - name of a file containing the described image
    author - the image's author (optional)
    universe - name of the universe to which the characters or scenery belong (optional)
    characters - a list of the characters involved (optional)
    tags - a list of tags associated with the image (optional)
    """

    img_id: UUID
    filename: str
    author: Optional[str]
    universe: Optional[str]
    characters: Optional[Iterable[str]]
    tags: Optional[Iterable[str]]
