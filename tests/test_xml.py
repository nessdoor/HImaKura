import unittest as ut
import uuid

import hik.xmngr as xm


class TestXMLCreation(ut.TestCase):
    def test_generate_minimal(self):
        img_id = uuid.UUID('03012ba3-086c-4604-bd6a-aa3e1a78f389')
        filename = "test.png"
        minimal_xml = xm.generate_xml(img_id, filename)
        expected = '<image id="{i}" filename="{f}" />'.format(i=img_id, f=filename)

        self.assertEqual(expected, minimal_xml)

    def test_generate_single_element_and_subtree(self):
        img_id = uuid.UUID('03012ba3-086c-4604-bd6a-aa3e1a78f389')
        filename = "test.png"
        universe = "unknown"
        tags = ["a", "b"]
        new_xml = xm.generate_xml(img_id, filename, universe=universe, tags=tags)
        expected = ('<image id="{i}" filename="{f}">' +
                    '<universe>{u}</universe>' +
                    '<tags><tag>{t1}</tag><tag>{t2}</tag></tags>' +
                    '</image>').format(i=img_id, f=filename, u=universe, t1=tags[0], t2=tags[1])

        self.assertEqual(expected, new_xml)
