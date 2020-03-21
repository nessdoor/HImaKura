from typing import NamedTuple, Optional, Iterable
from uuid import UUID


class ImageMetadata(NamedTuple):
    """An immutable object containing image metadata."""

    img_id: UUID
    filename: str
    author: Optional[str]
    universe: Optional[str]
    characters: Optional[Iterable[str]]
    tags: Optional[Iterable[str]]
