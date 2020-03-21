import xml.etree.ElementTree as ElTree
from typing import Iterable, Optional
from uuid import UUID

from common import ImageMetadata


def generate_xml(img_id: UUID,
                 filename: str,
                 author: Optional[str] = None,
                 universe: Optional[str] = None,
                 characters: Optional[Iterable[str]] = None,
                 tags: Optional[Iterable[str]] = None) -> str:
    """Generate a new XML document containing the metadata for a given image.

    :param img_id: a UUID identifying the image
    :param filename: name of a file containing the described image
    :param author: the image's author (optional)
    :param universe: name of the universe to which the characters or scenery belong (optional)
    :param characters: a list of the characters involved (optional)
    :param tags: a list of tags associated with the image (optional)
    :return: the generated XML in Unicode string format"""

    new_xml_root = ElTree.Element('image', {'id': str(img_id), 'filename': filename})

    if author is not None:
        ElTree.SubElement(new_xml_root, 'author').text = author

    if universe is not None:
        ElTree.SubElement(new_xml_root, 'universe').text = universe

    if characters is not None:
        section = ElTree.SubElement(new_xml_root, 'characters')
        for char in characters:
            ElTree.SubElement(section, 'character').text = char

    if tags is not None:
        section = ElTree.SubElement(new_xml_root, 'tags')
        for tag in tags:
            ElTree.SubElement(section, 'tag').text = tag

    return ElTree.tostring(new_xml_root, encoding="unicode")


def parse_xml(data: str) -> ImageMetadata:
    """Parse an XML containing image metadata.

    :param data: a string containing valid image metadata
    :return: an image metadata object"""

    image_elem = ElTree.fromstring(data)
    img_id = image_elem.get('id')
    filename = image_elem.get('filename')
    author = image_elem.find("./author")
    universe = image_elem.find("./universe")
    characters = [char.text for char in image_elem.findall("./characters/character")]
    tags = [tag.text for tag in image_elem.findall("./tags/tag")]

    return ImageMetadata(img_id=UUID(img_id),
                         filename=filename,
                         author=author.text if author is not None else None,
                         universe=universe.text if universe is not None else None,
                         characters=characters if len(characters) != 0 else None,
                         tags=tags if len(tags) != 0 else None)
