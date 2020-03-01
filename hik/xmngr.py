import xml.etree.ElementTree as ElTree
from typing import Union, Iterable
from uuid import UUID


def generate_xml(img_id: UUID,
                 filename: str,
                 author: Union[str, None] = None,
                 universe: Union[str, None] = None,
                 characters: Union[Iterable[str], None] = None,
                 tags: Union[Iterable[str], None] = None) -> str:
    """Generate a new XML document containing the metadata for a given image

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
