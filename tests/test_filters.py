import unittest as ut
from uuid import uuid4

from data.common import ImageMetadata
from data.filtering import FilterBuilder


class TestFilters(ut.TestCase):
    def test_empty_filter_single(self):
        # Check the effects of the absence of constraints on single-valued matchers
        el1 = ImageMetadata(uuid4(), 'xxx', None, None, None, None)
        el2 = ImageMetadata(uuid4(), 'kkk', None, None, None, None)

        empty_filter = FilterBuilder().get_id_filter()
        self.assertTrue(empty_filter(el1))
        self.assertTrue(empty_filter(el2))

    def test_empty_filter_collective(self):
        # Check the effects of the absence of constraints on multi-valued matchers
        el1 = ImageMetadata(uuid4(), 'xxx', None, None, None, ["nl", "ll"])
        el2 = ImageMetadata(uuid4(), 'kkk', None, None, None, None)

        empty_filter = FilterBuilder().get_tag_filter()
        self.assertTrue(empty_filter(el1))
        self.assertTrue(empty_filter(el2))

    def test_none_match_single(self):
        # Check the effects of None constraints on single-valued matchers
        el1 = ImageMetadata(uuid4(), 'fff', None, 'u', None, None)
        el2 = ImageMetadata(uuid4(), 'zzz', None, None, None, None)

        none_filter = FilterBuilder().universe_constraint(None).get_universe_filter()
        self.assertFalse(none_filter(el1))
        self.assertTrue(none_filter(el2))

    def test_none_match_collective(self):
        # Check the effects of None constraints on multi-valued matchers
        el1 = ImageMetadata(uuid4(), 'aaa', None, None, None, None)
        el2 = ImageMetadata(uuid4(), 'yyy', None, None, None, ["fta"])

        none_filter = FilterBuilder().tag_constraint(None).get_tag_filter()
        self.assertTrue(none_filter(el1))
        self.assertFalse(none_filter(el2))

    def test_single_element_filter(self):
        # Verify the effectiveness of single-valued matchers
        id1, filename1, author1, universe1 = uuid4(), "01.png", "bdhnd", "fotwf"
        id2, filename2, author2, universe2 = uuid4(), "02.jpg", "shndl", None
        id3, filename3, author3, universe3 = uuid4(), "03.png", "okn", "ph"

        el1 = ImageMetadata(id1, filename1, author1, universe1, None, None)
        el2 = ImageMetadata(id2, filename2, author2, universe2, None, None)
        el3 = ImageMetadata(id3, filename3, author3, universe3, None, None)

        filter_builder = FilterBuilder()

        # Test constraints satisfied
        filter_builder.filename_constraint(filename1).filename_constraint(filename2).filename_constraint(filename3)
        filename_filter = filter_builder.get_filename_filter()
        self.assertTrue(filename_filter(el1))
        self.assertTrue(filename_filter(el2))
        self.assertTrue(filename_filter(el3))

        # Test implicit exclusion
        filter_builder.author_constraint(author1)
        author_filter = filter_builder.get_author_filter()
        self.assertTrue(author_filter(el1))
        self.assertFalse(author_filter(el2))
        self.assertFalse(author_filter(el3))

        # Test explicit exclusion
        filter_builder.author_constraint(author2, True)
        author_filter = filter_builder.get_author_filter()
        self.assertTrue(author_filter(el1))
        self.assertFalse(author_filter(el2))
        self.assertTrue(author_filter(el3))

    def test_collective_conjunctive_filter(self):
        # Verify the effectiveness of multi-valued matchers, when evaluated in conjunction
        tags1 = ["y", "an", "hry"]
        tags2 = ["an", "mb", "sty", "rp"]
        tags3 = ["ll", "vnl"]

        el1 = ImageMetadata(uuid4(), "a.png", "ghi", None, None, tags1)
        el2 = ImageMetadata(uuid4(), "b.png", "nsh", None, None, tags2)
        el3 = ImageMetadata(uuid4(), "c.png", "ShT", None, None, tags3)

        filter_builder = FilterBuilder()

        # Test conjunctive filtering with inclusion
        f = filter_builder.tag_constraint("an").get_tag_filter()
        self.assertTrue(f(el1))
        self.assertTrue(f(el2))
        self.assertFalse(f(el3))

        # Test conjunctive filtering with exclusion
        f = filter_builder.tag_constraint("y", True).get_tag_filter()
        self.assertFalse(f(el1))
        self.assertTrue(f(el2))
        self.assertFalse((f(el3)))

    def test_collective_disjunctive_filter(self):
        # Verify the effectiveness of multi-valued matchers, when evaluated in disjunction
        chars1 = ["al", "john", "jack"]
        chars2 = ["jm", "jr"]
        chars3 = ["jr"]

        el1 = ImageMetadata(uuid4(), "a.png", "ghi", None, chars1, None)
        el2 = ImageMetadata(uuid4(), "b.png", "nsh", None, chars2, None)
        el3 = ImageMetadata(uuid4(), "c.png", "ShT", None, chars3, None)

        filter_builder = FilterBuilder()

        # Test disjunctive filtering with inclusion
        f = filter_builder.character_constraint("jm").character_constraint("al").characters_as_disjunctive(True) \
            .get_character_filter()
        self.assertTrue(f(el1))
        self.assertTrue(f(el2))
        self.assertFalse(f(el3))

        # Test disjunctive filtering with exclusion
        f = filter_builder.character_constraint("jack", True).get_character_filter()
        self.assertTrue(f(el1))
        self.assertTrue(f(el2))
        self.assertTrue(f(el3))

        filter_builder = FilterBuilder()
        f = filter_builder.characters_as_disjunctive(True).character_constraint("john", True) \
            .character_constraint("jack", True).get_character_filter()
        self.assertFalse(f(el1))
        self.assertTrue(f(el2))
        self.assertTrue(f(el3))
