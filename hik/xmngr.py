import xml.etree.ElementTree as ElTree
from uuid import UUID

from common import ImageMetadata


def generate_xml(metadata: ImageMetadata) -> str:
    """
    Generate a new XML document containing the metadata for a given image.

    :arg metadata: an image metadata object
    :return: the generated XML in Unicode string format
    """

    new_xml_root = ElTree.Element('image', {'id': str(metadata.img_id), 'filename': metadata.filename})

    if metadata.author is not None:
        ElTree.SubElement(new_xml_root, 'author').text = metadata.author

    if metadata.universe is not None:
        ElTree.SubElement(new_xml_root, 'universe').text = metadata.universe

    if metadata.characters is not None:
        section = ElTree.SubElement(new_xml_root, 'characters')
        for char in metadata.characters:
            ElTree.SubElement(section, 'character').text = char

    if metadata.tags is not None:
        section = ElTree.SubElement(new_xml_root, 'tags')
        for tag in metadata.tags:
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
