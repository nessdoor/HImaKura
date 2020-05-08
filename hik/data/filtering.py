from __future__ import annotations

from operator import attrgetter
from typing import Callable, Dict, Set, List, Optional, Iterable, TypeVar

from more_itertools import partition

from data.common import ImageMetadata


class FilterBuilder:
    """
    Builder for filters on image metadata.

    It supports creating filters for any property of `ImageMetadata` based on sets of included/excluded values. Some
    sets can be evaluated either in a conjunctive or disjunctive manner, that is: an image must satisfy all properties
    in that set or only some.

    Be careful with the logic intricacies caused by disjunctive sets.
    """

    class Constraint:
        def __init__(self, match: Optional[str], inverted: bool):
            self.match = match
            self.inverted = inverted

    class ConstraintsSet:
        def __init__(self, constraints: Set[FilterBuilder.Constraint], is_disjunctive: bool):
            self.constraints = constraints
            self.is_disjunctive = is_disjunctive

    def __init__(self):
        """Instantiate a new default builder."""

        self._sets: Dict[str, FilterBuilder.ConstraintsSet] = {}
        # TODO can this be made reflective on ImageMetadata?
        for field in ['img_id', 'filename', 'author', 'universe', 'characters', 'tags']:
            self._sets[field] = FilterBuilder.ConstraintsSet(set(), False)

        # Set disjunctive default as True for single-valued properties.
        self._sets['img_id'].is_disjunctive = True
        self._sets['filename'].is_disjunctive = True
        self._sets['author'].is_disjunctive = True
        self._sets['universe'].is_disjunctive = True

    def _set_constraint(self, constraints_set: str, match: Optional[str], exclude: bool) -> FilterBuilder:
        self._sets[constraints_set].constraints.add(FilterBuilder.Constraint(match, exclude))
        return self

    # TODO store info about property cardinality inside the unified structure
    # Generate filters for single-valued properties
    def _make_single_value_filter(self, constraints_set: str) -> Callable[[ImageMetadata], bool]:
        included, excluded = partition(attrgetter('inverted'), self._sets[constraints_set].constraints)
        included = frozenset(map(attrgetter('match'), included))
        excluded = frozenset(map(attrgetter('match'), excluded))

        # Filters for single-valued properties are only useful if disjunctive
        if len(excluded) > 0:
            # Negative matches in a disjunctive evaluation totally eclipse positive matches
            return lambda metadata: getattr(metadata, constraints_set) not in excluded
        else:
            if len(included) > 0:
                return lambda metadata: getattr(metadata, constraints_set) in included
            else:
                # No constraints have been specified: match anything
                return lambda _: True

    # Generate filters for multi-valued properties
    def _make_multi_value_filter(self, constraints_set: str) -> Callable[[ImageMetadata], bool]:
        T = TypeVar('T')

        def wrap_none(o: Optional[Iterable[T]]) -> Iterable[T]:
            return o if o is not None else [None]

        included, excluded = partition(attrgetter('inverted'), self._sets[constraints_set].constraints)
        included = frozenset(map(attrgetter('match'), included))
        excluded = frozenset(map(attrgetter('match'), excluded))

        if len(included) == 0 == len(excluded):
            # No constraints specified: match anything
            return lambda _: True
        elif self._sets[constraints_set].is_disjunctive:
            # Matched images must satisfy some positive constraints OR not satisfy at least one one negative constraint
            return lambda metadata: not included.isdisjoint(wrap_none(getattr(metadata, constraints_set))) \
                                    or not excluded.issubset(wrap_none(getattr(metadata, constraints_set)))
        else:
            # Matched images must satisfy all positive constraints AND not satisfy any negative constraint
            return lambda metadata: included.issubset(wrap_none(getattr(metadata, constraints_set))) \
                                    and excluded.isdisjoint(wrap_none(getattr(metadata, constraints_set)))

    def id_constraint(self, img_id: str, exclude: bool = False) -> FilterBuilder:
        """Set a disjunctive constraint on the ID."""

        return self._set_constraint('img_id', img_id, exclude)

    def get_id_filter(self) -> Callable[[ImageMetadata], bool]:
        """Get the ID filter."""

        return self._make_single_value_filter('img_id')

    def filename_constraint(self, filename: str, exclude: bool = False) -> FilterBuilder:
        """Set a disjunctive constraint on the file name."""

        return self._set_constraint('filename', filename, exclude)

    def get_filename_filter(self) -> Callable[[ImageMetadata], bool]:
        """Get the file name filter."""

        return self._make_single_value_filter('filename')

    def author_constraint(self, author: Optional[str], exclude: bool = False) -> FilterBuilder:
        """Set a disjunctive constraint on the author."""

        return self._set_constraint('author', author, exclude)

    def get_author_filter(self) -> Callable[[ImageMetadata], bool]:
        """Get the author filter."""

        return self._make_single_value_filter('author')

    def universe_constraint(self, universe: Optional[str], exclude: bool = False) -> FilterBuilder:
        """Set a disjunctive constraint on the universe."""

        return self._set_constraint('universe', universe, exclude)

    def get_universe_filter(self) -> Callable[[ImageMetadata], bool]:
        """Get the universe filter."""

        return self._make_single_value_filter('universe')

    def character_constraint(self, character: Optional[str], exclude: bool = False) -> FilterBuilder:
        """Set a constraint on characters."""

        return self._set_constraint('characters', character, exclude)

    def characters_as_disjunctive(self, flag: bool = False) -> FilterBuilder:
        """Toggle conjunctive/disjunctive evaluation of character constraints."""

        self._sets['characters'].is_disjunctive = flag
        return self

    def get_character_filter(self) -> Callable[[ImageMetadata], bool]:
        """Get the character filter."""

        return self._make_multi_value_filter('characters')

    def tag_constraint(self, tag: Optional[str], exclude: bool = False) -> FilterBuilder:
        """Set a constraint on tags."""

        return self._set_constraint('tags', tag, exclude)

    def tags_as_disjunctive(self, flag: bool = False) -> FilterBuilder:
        """Toggle conjunctive/disjunctive evaluation of tag constraints."""

        self._sets['tags'].is_disjunctive = flag
        return self

    def get_tag_filter(self) -> Callable[[ImageMetadata], bool]:
        """Get the tags filter."""

        return self._make_multi_value_filter('tags')

    def get_all_filters(self) -> List[Callable[[ImageMetadata], bool]]:
        """
        Generate a list of all the filters.

        Useful if you want to evaluate them in bulk with.
        """

        return [self.get_author_filter(), self.get_universe_filter(), self.get_character_filter(),
                self.get_tag_filter()]
