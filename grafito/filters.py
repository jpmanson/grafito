"""Advanced filter classes for Grafito query operations."""

import re
from typing import Any


from .exceptions import InvalidFilterError


class PropertyFilter:
    """Represents a property filter with comparison or pattern matching operators.

    This class provides a fluent API for creating advanced property filters
    that go beyond simple equality matching.

    Example:
        >>> PropertyFilter.gt(30)
        >>> PropertyFilter.contains('alice', case_sensitive=False)
        >>> PropertyFilter.between(25, 50)
    """

    def __init__(
        self,
        operator: str,
        value: Any,
        value2: Any = None,
        case_sensitive: bool = True,
        expected_type: type = None,
    ):
        """Initialize a property filter.

        Args:
            operator: Comparison or pattern operator (>, <, >=, <=, !=, BETWEEN,
                      CONTAINS, STARTS_WITH, ENDS_WITH, REGEX)
            value: Primary value for comparison/matching
            value2: Secondary value (used for BETWEEN)
            case_sensitive: For string matching, whether to be case-sensitive
            expected_type: Optional type validation (int, float, str, bool)

        Raises:
            InvalidFilterError: If type validation fails
        """
        self.operator = operator
        self.value = value
        self.value2 = value2
        self.case_sensitive = case_sensitive
        self.expected_type = expected_type

        if expected_type:
            self._validate_type(value, expected_type)
            if value2 is not None:
                self._validate_type(value2, expected_type)

    def _validate_type(self, val: Any, expected: type) -> None:
        """Validate value type matches expected type.

        Args:
            val: Value to validate
            expected: Expected type

        Raises:
            InvalidFilterError: If types don't match
        """
        if not isinstance(val, expected):
            raise InvalidFilterError(
                f"Expected {expected.__name__}, got {type(val).__name__}: {val}"
            )

    # Comparison Operators

    @staticmethod
    def gt(value: Any, expected_type: type = None) -> 'PropertyFilter':
        """Greater than operator.

        Args:
            value: Value to compare against
            expected_type: Optional type validation

        Returns:
            PropertyFilter with > operator

        Example:
            >>> db.match_nodes(properties={'age': PropertyFilter.gt(30)})
        """
        return PropertyFilter('>', value, expected_type=expected_type)

    @staticmethod
    def lt(value: Any, expected_type: type = None) -> 'PropertyFilter':
        """Less than operator.

        Args:
            value: Value to compare against
            expected_type: Optional type validation

        Returns:
            PropertyFilter with < operator

        Example:
            >>> db.match_nodes(properties={'score': PropertyFilter.lt(100)})
        """
        return PropertyFilter('<', value, expected_type=expected_type)

    @staticmethod
    def gte(value: Any, expected_type: type = None) -> 'PropertyFilter':
        """Greater than or equal operator.

        Args:
            value: Value to compare against
            expected_type: Optional type validation

        Returns:
            PropertyFilter with >= operator

        Example:
            >>> db.match_nodes(properties={'age': PropertyFilter.gte(18)})
        """
        return PropertyFilter('>=', value, expected_type=expected_type)

    @staticmethod
    def lte(value: Any, expected_type: type = None) -> 'PropertyFilter':
        """Less than or equal operator.

        Args:
            value: Value to compare against
            expected_type: Optional type validation

        Returns:
            PropertyFilter with <= operator

        Example:
            >>> db.match_nodes(properties={'rating': PropertyFilter.lte(5)})
        """
        return PropertyFilter('<=', value, expected_type=expected_type)

    @staticmethod
    def ne(value: Any, expected_type: type = None) -> 'PropertyFilter':
        """Not equal operator.

        Args:
            value: Value to compare against
            expected_type: Optional type validation

        Returns:
            PropertyFilter with != operator

        Example:
            >>> db.match_nodes(properties={'status': PropertyFilter.ne('deleted')})
        """
        return PropertyFilter('!=', value, expected_type=expected_type)

    @staticmethod
    def between(min_val: Any, max_val: Any, expected_type: type = None) -> 'PropertyFilter':
        """Between operator (inclusive range).

        Args:
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)
            expected_type: Optional type validation

        Returns:
            PropertyFilter with BETWEEN operator

        Example:
            >>> db.match_nodes(properties={'age': PropertyFilter.between(25, 35)})
        """
        return PropertyFilter('BETWEEN', min_val, max_val, expected_type=expected_type)

    # String Pattern Matching

    @staticmethod
    def contains(value: str, case_sensitive: bool = True) -> 'PropertyFilter':
        """Contains pattern matching (substring search).

        Args:
            value: Substring to search for
            case_sensitive: Whether matching is case-sensitive

        Returns:
            PropertyFilter with CONTAINS operator

        Example:
            >>> db.match_nodes(properties={
            ...     'name': PropertyFilter.contains('alice', case_sensitive=False)
            ... })
        """
        return PropertyFilter('CONTAINS', value, case_sensitive=case_sensitive)

    @staticmethod
    def starts_with(value: str, case_sensitive: bool = True) -> 'PropertyFilter':
        """Starts with pattern matching (prefix search).

        Args:
            value: Prefix to search for
            case_sensitive: Whether matching is case-sensitive

        Returns:
            PropertyFilter with STARTS_WITH operator

        Example:
            >>> db.match_nodes(properties={
            ...     'email': PropertyFilter.starts_with('john')
            ... })
        """
        return PropertyFilter('STARTS_WITH', value, case_sensitive=case_sensitive)

    @staticmethod
    def ends_with(value: str, case_sensitive: bool = True) -> 'PropertyFilter':
        """Ends with pattern matching (suffix search).

        Args:
            value: Suffix to search for
            case_sensitive: Whether matching is case-sensitive

        Returns:
            PropertyFilter with ENDS_WITH operator

        Example:
            >>> db.match_nodes(properties={
            ...     'email': PropertyFilter.ends_with('@gmail.com')
            ... })
        """
        return PropertyFilter('ENDS_WITH', value, case_sensitive=case_sensitive)

    @staticmethod
    def regex(pattern: str) -> 'PropertyFilter':
        """Regular expression pattern matching.

        Args:
            pattern: Regex pattern to match

        Returns:
            PropertyFilter with REGEX operator

        Example:
            >>> db.match_nodes(properties={
            ...     'phone': PropertyFilter.regex(r'^\\d{3}-\\d{3}-\\d{4}$')
            ... })

        Note:
            Regex matching can be slow on large datasets. Consider using
            LIKE-based patterns (contains, starts_with, ends_with) when possible.
            Invalid regex patterns will not raise an error during filter creation,
            but will return no matches during query execution.
        """
        try:
            re.compile(pattern)
        except re.error as exc:
            raise InvalidFilterError(f"Invalid regex pattern: {exc}") from exc
        return PropertyFilter('REGEX', pattern)


class LabelFilter:
    """Filter for label matching with AND/OR logic.

    By default, passing a list of labels to match_nodes uses AND logic
    (node must have ALL labels). LabelFilter provides explicit control.

    Example:
        >>> LabelFilter.any(['Person', 'Company'])  # Person OR Company
        >>> LabelFilter.all(['Person', 'Employee'])  # Person AND Employee (explicit)
    """

    def __init__(self, operator: str, labels: list[str]):
        """Initialize a label filter.

        Args:
            operator: 'OR' or 'AND'
            labels: List of label names

        Raises:
            InvalidFilterError: If operator is invalid or labels is empty
        """
        if operator not in ('OR', 'AND'):
            raise InvalidFilterError(f"Invalid label filter operator: {operator}")
        if not labels:
            raise InvalidFilterError("Label filter requires at least one label")

        self.operator = operator
        self.labels = labels

    @staticmethod
    def any(labels: list[str]) -> 'LabelFilter':
        """Create OR filter (match nodes with ANY of the labels).

        Args:
            labels: List of label names

        Returns:
            LabelFilter with OR operator

        Example:
            >>> db.match_nodes(labels=LabelFilter.any(['Person', 'Company']))
        """
        return LabelFilter('OR', labels)

    @staticmethod
    def all(labels: list[str]) -> 'LabelFilter':
        """Create AND filter (match nodes with ALL of the labels).

        Args:
            labels: List of label names

        Returns:
            LabelFilter with AND operator

        Example:
            >>> db.match_nodes(labels=LabelFilter.all(['Person', 'Employee']))

        Note:
            This is equivalent to passing a plain list, but more explicit.
        """
        return LabelFilter('AND', labels)


class PropertyFilterGroup:
    """Group of property filters combined with AND/OR logic.

    Allows complex boolean expressions for property matching.

    Example:
        >>> PropertyFilterGroup.or_(
        ...     {'city': 'NYC'},
        ...     {'city': 'LA'}
        ... )
        >>> PropertyFilterGroup.and_(
        ...     {'age': PropertyFilter.gt(30)},
        ...     {'city': 'NYC'}
        ... )
    """

    def __init__(self, operator: str, *filters: dict):
        """Initialize a property filter group.

        Args:
            operator: 'OR' or 'AND'
            *filters: Property dictionaries to combine

        Raises:
            InvalidFilterError: If operator is invalid or no filters provided
        """
        if operator not in ('OR', 'AND'):
            raise InvalidFilterError(f"Invalid filter group operator: {operator}")
        if not filters:
            raise InvalidFilterError("Filter group requires at least one filter")

        self.operator = operator
        self.filters = filters

    @staticmethod
    def or_(*filters: dict) -> 'PropertyFilterGroup':
        """Create OR group (match if ANY filter matches).

        Args:
            *filters: Property filter dictionaries

        Returns:
            PropertyFilterGroup with OR operator

        Example:
            >>> db.match_nodes(properties=PropertyFilterGroup.or_(
            ...     {'city': 'NYC'},
            ...     {'city': 'LA'},
            ...     {'city': 'SF'}
            ... ))
        """
        return PropertyFilterGroup('OR', *filters)

    @staticmethod
    def and_(*filters: dict) -> 'PropertyFilterGroup':
        """Create AND group (match if ALL filters match).

        Args:
            *filters: Property filter dictionaries

        Returns:
            PropertyFilterGroup with AND operator

        Example:
            >>> db.match_nodes(properties=PropertyFilterGroup.and_(
            ...     {'age': PropertyFilter.gt(30)},
            ...     {'city': 'NYC'}
            ... ))

        Note:
            For simple AND combinations, you can just pass multiple properties
            in the same dict. This is useful for nested combinations.
        """
        return PropertyFilterGroup('AND', *filters)


class SortOrder:
    """Specification for ordering query results by property.

    Example:
        >>> SortOrder('age', ascending=True)
        >>> SortOrder('name', ascending=False)
    """

    def __init__(self, property: str, ascending: bool = True):
        """Initialize a sort order specification.

        Args:
            property: Property name to sort by
            ascending: True for ASC, False for DESC

        Raises:
            InvalidFilterError: If property name is empty
        """
        if not property:
            raise InvalidFilterError("Sort property name cannot be empty")

        self.property = property
        self.ascending = ascending

    def to_sql(self, table_alias: str = 'n') -> str:
        """Convert to SQL ORDER BY clause fragment.

        Args:
            table_alias: Table alias to use in json_extract

        Returns:
            SQL fragment like "json_extract(n.properties, '$.age') ASC"
        """
        direction = 'ASC' if self.ascending else 'DESC'
        return f"json_extract({table_alias}.properties, '$.{self.property}') {direction}"

    def __repr__(self) -> str:
        """String representation."""
        direction = 'ASC' if self.ascending else 'DESC'
        return f"SortOrder('{self.property}', {direction})"
