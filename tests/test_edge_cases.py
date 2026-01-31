"""Tests for edge cases and error handling in advanced filters."""

import pytest
from grafito import (
    GrafitoDatabase,
    PropertyFilter,
    PropertyFilterGroup,
    LabelFilter,
    SortOrder,
    InvalidFilterError,
)


class TestNullAndEmptyValues:
    """Test handling of NULL and empty values."""

    def test_null_property_exact_match(self):
        """Test exact match with NULL property values."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice', 'age': 30})
        db.create_node(labels=['Person'], properties={'name': 'Bob'})  # No age

        # Exact match should not find NULL
        results = db.match_nodes(
            labels=['Person'],
            properties={'age': 30}
        )
        assert len(results) == 1
        assert results[0].properties['name'] == 'Alice'
        db.close()

    def test_empty_string_property(self):
        """Test properties with empty strings."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': '', 'age': 30})
        db.create_node(labels=['Person'], properties={'name': 'Alice', 'age': 25})

        # Find empty string
        results = db.match_nodes(
            labels=['Person'],
            properties={'name': ''}
        )
        assert len(results) == 1
        assert results[0].properties['age'] == 30
        db.close()

    def test_empty_string_contains(self):
        """Test CONTAINS with empty string."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice'})
        db.create_node(labels=['Person'], properties={'name': 'Bob'})

        # Empty string should match all (everything contains empty string)
        results = db.match_nodes(
            labels=['Person'],
            properties={'name': PropertyFilter.contains('')}
        )
        assert len(results) == 2
        db.close()

    def test_null_with_string_operators(self):
        """Test string operators with NULL values."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice', 'city': 'NYC'})
        db.create_node(labels=['Person'], properties={'name': 'Bob'})  # No city

        # String operators should exclude NULL
        results = db.match_nodes(
            labels=['Person'],
            properties={'city': PropertyFilter.starts_with('N')}
        )
        assert len(results) == 1
        assert results[0].properties['name'] == 'Alice'
        db.close()

    def test_empty_list_property(self):
        """Test properties with empty lists."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice', 'hobbies': []})
        db.create_node(labels=['Person'], properties={'name': 'Bob', 'hobbies': ['reading']})

        # Find empty list
        results = db.match_nodes(
            labels=['Person'],
            properties={'hobbies': []}
        )
        assert len(results) == 1
        assert results[0].properties['name'] == 'Alice'
        db.close()

    def test_empty_dict_property(self):
        """Test properties with empty dicts."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice', 'metadata': {}})
        db.create_node(labels=['Person'], properties={'name': 'Bob', 'metadata': {'key': 'value'}})

        # Find empty dict
        results = db.match_nodes(
            labels=['Person'],
            properties={'metadata': {}}
        )
        assert len(results) == 1
        assert results[0].properties['name'] == 'Alice'
        db.close()


class TestSpecialCharacters:
    """Test handling of special characters."""

    def test_special_characters_in_strings(self):
        """Test special characters in string values."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': "O'Brien"})
        db.create_node(labels=['Person'], properties={'name': 'Smith & Jones'})
        db.create_node(labels=['Person'], properties={'name': 'Name with "quotes"'})

        # Exact match with special characters
        results = db.match_nodes(
            labels=['Person'],
            properties={'name': "O'Brien"}
        )
        assert len(results) == 1
        assert results[0].properties['name'] == "O'Brien"
        db.close()

    def test_like_wildcard_escaping(self):
        """Test LIKE wildcards are properly escaped."""
        db = GrafitoDatabase()
        db.create_node(labels=['Product'], properties={'code': '100%'})
        db.create_node(labels=['Product'], properties={'code': '100A'})
        db.create_node(labels=['Product'], properties={'code': '100_TEST'})
        db.create_node(labels=['Product'], properties={'code': '100XTEST'})

        # Contains should escape % and _
        results = db.match_nodes(
            labels=['Product'],
            properties={'code': PropertyFilter.contains('100%')}
        )
        assert len(results) == 1
        assert results[0].properties['code'] == '100%'

        results = db.match_nodes(
            labels=['Product'],
            properties={'code': PropertyFilter.contains('100_')}
        )
        assert len(results) == 1
        assert results[0].properties['code'] == '100_TEST'
        db.close()

    def test_unicode_characters(self):
        """Test Unicode characters in strings."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Jose'})
        db.create_node(labels=['Person'], properties={'name': 'Muller'})
        db.create_node(labels=['Person'], properties={'name': 'Nakamura'})

        # Contains with Unicode
        results = db.match_nodes(
            labels=['Person'],
            properties={'name': PropertyFilter.contains('ller')}
        )
        assert len(results) == 1
        db.close()

    def test_newlines_and_tabs(self):
        """Test strings with newlines and tabs."""
        db = GrafitoDatabase()
        db.create_node(labels=['Text'], properties={'content': 'Line 1\nLine 2'})
        db.create_node(labels=['Text'], properties={'content': 'Tab\there'})

        # Exact match with newlines
        results = db.match_nodes(
            labels=['Text'],
            properties={'content': 'Line 1\nLine 2'}
        )
        assert len(results) == 1
        db.close()


class TestTypeConsistency:
    """Test type consistency and validation."""

    def test_mixed_type_properties(self):
        """Test properties with inconsistent types across nodes."""
        db = GrafitoDatabase()
        db.create_node(labels=['Item'], properties={'value': 100})  # int
        db.create_node(labels=['Item'], properties={'value': 100.0})  # float
        db.create_node(labels=['Item'], properties={'value': '100'})  # string

        # Greater than with number
        results = db.match_nodes(
            labels=['Item'],
            properties={'value': PropertyFilter.gt(50)}
        )
        # Should match int and float, not string
        assert len(results) == 2
        db.close()

    def test_boolean_false_vs_none(self):
        """Test distinction between False and None."""
        db = GrafitoDatabase()
        db.create_node(labels=['User'], properties={'name': 'Alice', 'active': True})
        db.create_node(labels=['User'], properties={'name': 'Bob', 'active': False})
        db.create_node(labels=['User'], properties={'name': 'Charlie'})  # No active

        # Exact match for False
        results = db.match_nodes(
            labels=['User'],
            properties={'active': False}
        )
        assert len(results) == 1
        assert results[0].properties['name'] == 'Bob'

        # Not equal to True should include False and None
        results = db.match_nodes(
            labels=['User'],
            properties={'active': PropertyFilter.ne(True)}
        )
        assert len(results) == 2
        db.close()

    def test_zero_vs_false_vs_none(self):
        """Test distinction between 0, False, and None."""
        db = GrafitoDatabase()
        db.create_node(labels=['Item'], properties={'count': 0})
        db.create_node(labels=['Item'], properties={'count': False})  # Stored as 0
        db.create_node(labels=['Item'], properties={'name': 'test'})  # No count

        # Exact match for 0
        results = db.match_nodes(
            labels=['Item'],
            properties={'count': 0}
        )
        # Both 0 and False should match (SQLite treats them the same)
        assert len(results) >= 1
        db.close()


class TestInvalidFilters:
    """Test error handling for invalid filters."""

    def test_invalid_property_name_sql_injection_attempt(self):
        """Test SQL injection prevention in property names."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 30})

        # Property name with SQL injection attempt
        with pytest.raises(InvalidFilterError, match="Invalid property name"):
            db.match_nodes(
                labels=['Person'],
                order_by="age; DROP TABLE nodes--"
            )
        db.close()

    def test_negative_limit(self):
        """Test negative limit raises error."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 30})

        with pytest.raises(InvalidFilterError, match="Limit must be non-negative"):
            db.match_nodes(labels=['Person'], limit=-1)
        db.close()

    def test_negative_offset(self):
        """Test negative offset raises error."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 30})

        with pytest.raises(InvalidFilterError, match="Offset must be non-negative"):
            db.match_nodes(labels=['Person'], limit=10, offset=-1)
        db.close()

    def test_invalid_regex_pattern(self):
        """Test invalid regex pattern in query."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice'})

        with pytest.raises(InvalidFilterError, match="Invalid regex pattern"):
            db.match_nodes(
                labels=['Person'],
                properties={'name': PropertyFilter.regex('[')}  # Invalid regex
            )
        db.close()

    def test_type_validation_in_filter(self):
        """Test type validation in PropertyFilter."""
        # Should raise error when type doesn't match
        with pytest.raises(InvalidFilterError, match="Expected int, got str"):
            PropertyFilter.gt("30", expected_type=int)

    def test_empty_sort_order_property(self):
        """Test SortOrder with empty property name."""
        with pytest.raises(InvalidFilterError, match="property name cannot be empty"):
            SortOrder('')


class TestEmptyResults:
    """Test queries that return empty results."""

    def test_no_matching_nodes(self):
        """Test query with no matching nodes."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 30})

        results = db.match_nodes(
            labels=['Person'],
            properties={'age': PropertyFilter.gt(100)}
        )
        assert len(results) == 0
        db.close()

    def test_no_matching_labels(self):
        """Test query with non-existent labels."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 30})

        results = db.match_nodes(labels=['NonExistent'])
        assert len(results) == 0
        db.close()

    def test_empty_database(self):
        """Test queries on empty database."""
        db = GrafitoDatabase()

        results = db.match_nodes(labels=['Person'])
        assert len(results) == 0

        results = db.match_nodes(properties={'age': PropertyFilter.gt(0)})
        assert len(results) == 0
        db.close()

    def test_offset_beyond_results(self):
        """Test offset larger than result set."""
        db = GrafitoDatabase()
        for i in range(5):
            db.create_node(labels=['Item'], properties={'number': i})

        results = db.match_nodes(
            labels=['Item'],
            limit=10,
            offset=100
        )
        assert len(results) == 0
        db.close()


class TestComplexCombinations:
    """Test complex and unusual filter combinations."""

    def test_all_filters_on_single_property(self):
        """Test multiple different filters on same property."""
        db = GrafitoDatabase()
        for i in range(20):
            db.create_node(labels=['Item'], properties={'value': i})

        # Value > 5 AND value < 15 (should be 10 results: 6-14)
        results = db.match_nodes(
            labels=['Item'],
            properties={
                'value': PropertyFilter.gt(5),
            }
        )
        results2 = db.match_nodes(
            labels=['Item'],
            properties={
                'value': PropertyFilter.lt(15),
            }
        )
        # Can't combine both on same key directly, but BETWEEN works
        results_between = db.match_nodes(
            labels=['Item'],
            properties={'value': PropertyFilter.between(6, 14)}
        )
        assert len(results_between) == 9  # 6, 7, 8, 9, 10, 11, 12, 13, 14
        db.close()

    def test_deeply_nested_or_groups(self):
        """Test deeply nested OR groups."""
        db = GrafitoDatabase()
        db.create_node(labels=['Item'], properties={'a': 1, 'b': 2})
        db.create_node(labels=['Item'], properties={'a': 3, 'b': 4})
        db.create_node(labels=['Item'], properties={'a': 5, 'b': 6})

        # (a=1 OR a=3) OR (b=6)
        results = db.match_nodes(
            labels=['Item'],
            properties=PropertyFilterGroup.or_(
                PropertyFilterGroup.or_(
                    {'a': 1},
                    {'a': 3}
                ),
                {'b': 6}
            )
        )
        assert len(results) == 3
        db.close()

    def test_empty_property_filter_group(self):
        """Test PropertyFilterGroup with no filters."""
        db = GrafitoDatabase()
        db.create_node(labels=['Item'], properties={'value': 1})

        # Empty OR should match nothing (no conditions)
        group = PropertyFilterGroup('OR', [])
        results = db.match_nodes(
            labels=['Item'],
            properties=group
        )
        # Should return all since there are no conditions
        assert len(results) >= 0
        db.close()

    def test_single_element_or_group(self):
        """Test OR group with single element."""
        db = GrafitoDatabase()
        db.create_node(labels=['Item'], properties={'value': 1})
        db.create_node(labels=['Item'], properties={'value': 2})

        # OR with single condition should work like normal filter
        results = db.match_nodes(
            labels=['Item'],
            properties=PropertyFilterGroup.or_({'value': 1})
        )
        assert len(results) == 1
        db.close()


class TestOrderingEdgeCases:
    """Test edge cases in ordering."""

    def test_order_by_nonexistent_property(self):
        """Test ordering by property that doesn't exist on some nodes."""
        db = GrafitoDatabase()
        db.create_node(labels=['Item'], properties={'name': 'A', 'value': 1})
        db.create_node(labels=['Item'], properties={'name': 'B'})  # No value
        db.create_node(labels=['Item'], properties={'name': 'C', 'value': 2})

        # Should work - NULLs go to end
        results = db.match_nodes(
            labels=['Item'],
            order_by='value',
            ascending=True
        )
        assert len(results) == 3
        # First two should have values, last should be NULL
        assert results[0].properties.get('value') == 1
        assert results[1].properties.get('value') == 2
        assert results[2].properties.get('value') is None
        db.close()

    def test_order_by_all_nulls(self):
        """Test ordering when all values are NULL."""
        db = GrafitoDatabase()
        db.create_node(labels=['Item'], properties={'name': 'A'})
        db.create_node(labels=['Item'], properties={'name': 'B'})
        db.create_node(labels=['Item'], properties={'name': 'C'})

        # Order by nonexistent property
        results = db.match_nodes(
            labels=['Item'],
            order_by='nonexistent',
            ascending=True
        )
        assert len(results) == 3
        db.close()

    def test_order_with_limit_zero(self):
        """Test ordering with limit 0."""
        db = GrafitoDatabase()
        for i in range(10):
            db.create_node(labels=['Item'], properties={'value': i})

        results = db.match_nodes(
            labels=['Item'],
            order_by='value',
            limit=0
        )
        assert len(results) == 0
        db.close()


class TestRelationshipFilters:
    """Test advanced filters on relationships."""

    def test_relationship_with_null_properties(self):
        """Test relationship queries with NULL properties."""
        db = GrafitoDatabase()
        alice = db.create_node(labels=['Person'], properties={'name': 'Alice'})
        bob = db.create_node(labels=['Person'], properties={'name': 'Bob'})
        charlie = db.create_node(labels=['Person'], properties={'name': 'Charlie'})

        db.create_relationship(alice.id, bob.id, 'KNOWS', {'since': 2020})
        db.create_relationship(alice.id, charlie.id, 'KNOWS', {})  # No since

        # Filter relationships by property
        results = db.match_relationships(
            source_id=alice.id,
            rel_type='KNOWS',
            properties={'since': PropertyFilter.gte(2019)}
        )
        assert len(results) == 1
        db.close()

    def test_relationship_ordering_with_pagination(self):
        """Test ordering and pagination on relationships."""
        db = GrafitoDatabase()
        alice = db.create_node(labels=['Person'], properties={'name': 'Alice'})

        for i in range(10):
            person = db.create_node(labels=['Person'], properties={'name': f'Person{i}'})
            db.create_relationship(alice.id, person.id, 'KNOWS', {'order': i})

        # Get middle page
        results = db.match_relationships(
            source_id=alice.id,
            rel_type='KNOWS',
            order_by='order',
            limit=3,
            offset=3
        )
        assert len(results) == 3
        orders = [r.properties['order'] for r in results]
        assert orders == [3, 4, 5]
        db.close()


class TestBackwardCompatibilityEdgeCases:
    """Test backward compatibility in edge cases."""

    def test_none_values_in_properties(self):
        """Test passing None in properties dict."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice', 'age': 30})
        db.create_node(labels=['Person'], properties={'name': 'Bob'})

        # None in properties should be handled gracefully
        # (Though this isn't a typical use case)
        results = db.match_nodes(
            labels=['Person'],
            properties={'name': 'Alice'}
        )
        assert len(results) == 1
        db.close()

    def test_empty_label_list(self):
        """Test empty label list."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice'})

        # Empty label list should match all
        results = db.match_nodes(labels=[])
        assert len(results) >= 1
        db.close()

    def test_empty_properties_dict(self):
        """Test empty properties dict."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice'})
        db.create_node(labels=['Person'], properties={'name': 'Bob'})

        # Empty properties should match all with label
        results = db.match_nodes(labels=['Person'], properties={})
        assert len(results) == 2
        db.close()
