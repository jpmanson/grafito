"""Tests for OR logic in advanced filters."""

import pytest
from grafito import (
    GrafitoDatabase,
    PropertyFilter,
    PropertyFilterGroup,
    LabelFilter,
    InvalidFilterError
)


class TestLabelOR:
    """Test OR logic for labels."""

    def test_label_or_two_labels(self):
        """Test OR with two labels."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice'})
        db.create_node(labels=['Company'], properties={'name': 'TechCorp'})
        db.create_node(labels=['Product'], properties={'name': 'Laptop'})

        results = db.match_nodes(
            labels=LabelFilter.any(['Person', 'Company'])
        )

        assert len(results) == 2
        db.close()

    def test_label_or_three_labels(self):
        """Test OR with three labels."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice'})
        db.create_node(labels=['Company'], properties={'name': 'TechCorp'})
        db.create_node(labels=['Product'], properties={'name': 'Laptop'})
        db.create_node(labels=['Location'], properties={'name': 'NYC'})

        results = db.match_nodes(
            labels=LabelFilter.any(['Person', 'Company', 'Product'])
        )

        assert len(results) == 3
        db.close()

    def test_label_or_with_properties(self):
        """Test OR labels combined with property filters."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice', 'city': 'NYC'})
        db.create_node(labels=['Company'], properties={'name': 'TechCorp', 'city': 'NYC'})
        db.create_node(labels=['Person'], properties={'name': 'Bob', 'city': 'LA'})
        db.create_node(labels=['Product'], properties={'name': 'Laptop', 'city': 'NYC'})

        results = db.match_nodes(
            labels=LabelFilter.any(['Person', 'Company']),
            properties={'city': 'NYC'}
        )

        assert len(results) == 2
        names = sorted([n.properties['name'] for n in results])
        assert names == ['Alice', 'TechCorp']
        db.close()

    def test_label_or_no_match(self):
        """Test OR labels with no matching nodes."""
        db = GrafitoDatabase()
        db.create_node(labels=['Product'], properties={'name': 'Laptop'})
        db.create_node(labels=['Product'], properties={'name': 'Mouse'})

        results = db.match_nodes(
            labels=LabelFilter.any(['Person', 'Company'])
        )

        assert len(results) == 0
        db.close()

    def test_label_all_explicit_and(self):
        """Test LabelFilter.all() for explicit AND."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person', 'Employee'], properties={'name': 'Alice'})
        db.create_node(labels=['Person'], properties={'name': 'Bob'})
        db.create_node(labels=['Employee'], properties={'name': 'Charlie'})

        results = db.match_nodes(
            labels=LabelFilter.all(['Person', 'Employee'])
        )

        assert len(results) == 1
        assert results[0].properties['name'] == 'Alice'
        db.close()

    def test_label_or_vs_and(self):
        """Test difference between OR and AND for labels."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person', 'Employee'], properties={'name': 'Alice'})
        db.create_node(labels=['Person'], properties={'name': 'Bob'})
        db.create_node(labels=['Employee'], properties={'name': 'Charlie'})

        # OR: nodes with ANY of the labels
        or_results = db.match_nodes(
            labels=LabelFilter.any(['Person', 'Employee'])
        )
        assert len(or_results) == 3

        # AND: nodes with ALL labels (backward compatible)
        and_results = db.match_nodes(
            labels=['Person', 'Employee']
        )
        assert len(and_results) == 1
        db.close()

    def test_label_filter_empty_list_error(self):
        """Test LabelFilter raises error with empty list."""
        with pytest.raises(InvalidFilterError, match="at least one label"):
            LabelFilter.any([])

    def test_label_filter_invalid_operator(self):
        """Test LabelFilter raises error with invalid operator."""
        with pytest.raises(InvalidFilterError, match="Invalid label filter operator"):
            LabelFilter('INVALID', ['Person'])


class TestPropertyOR:
    """Test OR logic for properties."""

    def test_property_or_two_values(self):
        """Test OR with two property values."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'city': 'NYC'})
        db.create_node(labels=['Person'], properties={'city': 'LA'})
        db.create_node(labels=['Person'], properties={'city': 'SF'})

        results = db.match_nodes(
            labels=['Person'],
            properties=PropertyFilterGroup.or_(
                {'city': 'NYC'},
                {'city': 'LA'}
            )
        )

        assert len(results) == 2
        cities = sorted([n.properties['city'] for n in results])
        assert cities == ['LA', 'NYC']
        db.close()

    def test_property_or_three_values(self):
        """Test OR with three property values."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'city': 'NYC'})
        db.create_node(labels=['Person'], properties={'city': 'LA'})
        db.create_node(labels=['Person'], properties={'city': 'SF'})
        db.create_node(labels=['Person'], properties={'city': 'Chicago'})

        results = db.match_nodes(
            labels=['Person'],
            properties=PropertyFilterGroup.or_(
                {'city': 'NYC'},
                {'city': 'LA'},
                {'city': 'SF'}
            )
        )

        assert len(results) == 3
        db.close()

    def test_property_or_different_properties(self):
        """Test OR with different property names."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice', 'age': 30})
        db.create_node(labels=['Person'], properties={'name': 'Bob', 'age': 25})
        db.create_node(labels=['Person'], properties={'name': 'Charlie', 'age': 30})

        results = db.match_nodes(
            labels=['Person'],
            properties=PropertyFilterGroup.or_(
                {'name': 'Alice'},
                {'age': 25}
            )
        )

        assert len(results) == 2
        names = sorted([n.properties['name'] for n in results])
        assert names == ['Alice', 'Bob']
        db.close()

    def test_property_or_with_comparison_operators(self):
        """Test OR with comparison operators."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 20})
        db.create_node(labels=['Person'], properties={'age': 30})
        db.create_node(labels=['Person'], properties={'age': 40})

        results = db.match_nodes(
            labels=['Person'],
            properties=PropertyFilterGroup.or_(
                {'age': PropertyFilter.lt(25)},
                {'age': PropertyFilter.gt(35)}
            )
        )

        assert len(results) == 2
        ages = sorted([n.properties['age'] for n in results])
        assert ages == [20, 40]
        db.close()

    def test_property_and_explicit(self):
        """Test PropertyFilterGroup.and_() for explicit AND."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 30, 'city': 'NYC'})
        db.create_node(labels=['Person'], properties={'age': 30, 'city': 'LA'})
        db.create_node(labels=['Person'], properties={'age': 25, 'city': 'NYC'})

        results = db.match_nodes(
            labels=['Person'],
            properties=PropertyFilterGroup.and_(
                {'age': 30},
                {'city': 'NYC'}
            )
        )

        assert len(results) == 1
        assert results[0].properties['age'] == 30
        assert results[0].properties['city'] == 'NYC'
        db.close()

    def test_property_or_no_match(self):
        """Test OR with no matching nodes."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'city': 'Chicago'})
        db.create_node(labels=['Person'], properties={'city': 'Boston'})

        results = db.match_nodes(
            labels=['Person'],
            properties=PropertyFilterGroup.or_(
                {'city': 'NYC'},
                {'city': 'LA'}
            )
        )

        assert len(results) == 0
        db.close()

    def test_property_filter_group_empty_error(self):
        """Test PropertyFilterGroup raises error with no filters."""
        with pytest.raises(InvalidFilterError, match="at least one filter"):
            PropertyFilterGroup.or_()

    def test_property_filter_group_invalid_operator(self):
        """Test PropertyFilterGroup raises error with invalid operator."""
        with pytest.raises(InvalidFilterError, match="Invalid filter group operator"):
            PropertyFilterGroup('INVALID', {'city': 'NYC'})


class TestNestedORLogic:
    """Test nested OR/AND combinations."""

    def test_nested_or_groups(self):
        """Test nested OR groups."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice', 'city': 'NYC', 'age': 30})
        db.create_node(labels=['Person'], properties={'name': 'Bob', 'city': 'LA', 'age': 25})
        db.create_node(labels=['Person'], properties={'name': 'Charlie', 'city': 'NYC', 'age': 35})
        db.create_node(labels=['Person'], properties={'name': 'Diana', 'city': 'SF', 'age': 30})

        # (city=NYC OR city=LA) AND age=30
        # But we can't express this directly with current API, so test separately
        nyc_or_la = db.match_nodes(
            labels=['Person'],
            properties=PropertyFilterGroup.or_(
                {'city': 'NYC'},
                {'city': 'LA'}
            )
        )
        assert len(nyc_or_la) == 3

        age_30 = db.match_nodes(
            labels=['Person'],
            properties={'age': 30}
        )
        assert len(age_30) == 2
        db.close()

    def test_or_with_multiple_properties_each(self):
        """Test OR where each filter has multiple properties (AND within, OR between)."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'city': 'NYC', 'age': 30})
        db.create_node(labels=['Person'], properties={'city': 'NYC', 'age': 25})
        db.create_node(labels=['Person'], properties={'city': 'LA', 'age': 30})
        db.create_node(labels=['Person'], properties={'city': 'LA', 'age': 35})

        # (city=NYC AND age=30) OR (city=LA AND age=35)
        results = db.match_nodes(
            labels=['Person'],
            properties=PropertyFilterGroup.or_(
                {'city': 'NYC', 'age': 30},
                {'city': 'LA', 'age': 35}
            )
        )

        assert len(results) == 2
        db.close()


class TestCombinedLogic:
    """Test combining label OR with property OR."""

    def test_label_or_with_property_or(self):
        """Test combining label OR with property OR."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'city': 'NYC'})
        db.create_node(labels=['Person'], properties={'city': 'LA'})
        db.create_node(labels=['Company'], properties={'city': 'NYC'})
        db.create_node(labels=['Company'], properties={'city': 'SF'})
        db.create_node(labels=['Product'], properties={'city': 'NYC'})

        results = db.match_nodes(
            labels=LabelFilter.any(['Person', 'Company']),
            properties=PropertyFilterGroup.or_(
                {'city': 'NYC'},
                {'city': 'LA'}
            )
        )

        assert len(results) == 3
        db.close()

    def test_label_or_with_comparison_filters(self):
        """Test label OR with comparison operators."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 25})
        db.create_node(labels=['Person'], properties={'age': 35})
        db.create_node(labels=['Company'], properties={'age': 30})  # Company age (years in business)
        db.create_node(labels=['Company'], properties={'age': 40})

        results = db.match_nodes(
            labels=LabelFilter.any(['Person', 'Company']),
            properties={'age': PropertyFilter.gte(30)}
        )

        assert len(results) == 3
        ages = sorted([n.properties['age'] for n in results])
        assert ages == [30, 35, 40]
        db.close()

    def test_label_and_with_property_or(self):
        """Test label AND (default) with property OR."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person', 'Employee'], properties={'city': 'NYC'})
        db.create_node(labels=['Person', 'Employee'], properties={'city': 'LA'})
        db.create_node(labels=['Person'], properties={'city': 'NYC'})
        db.create_node(labels=['Employee'], properties={'city': 'LA'})

        results = db.match_nodes(
            labels=['Person', 'Employee'],  # Must have BOTH labels
            properties=PropertyFilterGroup.or_(
                {'city': 'NYC'},
                {'city': 'LA'}
            )
        )

        assert len(results) == 2
        db.close()


class TestORWithRelationships:
    """Test OR logic with relationships."""

    def test_relationship_property_or(self):
        """Test OR logic on relationship properties."""
        db = GrafitoDatabase()
        alice = db.create_node(labels=['Person'], properties={'name': 'Alice'})
        bob = db.create_node(labels=['Person'], properties={'name': 'Bob'})
        charlie = db.create_node(labels=['Person'], properties={'name': 'Charlie'})
        diana = db.create_node(labels=['Person'], properties={'name': 'Diana'})

        db.create_relationship(alice.id, bob.id, 'KNOWS', {'since': 2015})
        db.create_relationship(alice.id, charlie.id, 'KNOWS', {'since': 2020})
        db.create_relationship(alice.id, diana.id, 'KNOWS', {'since': 2018})

        results = db.match_relationships(
            source_id=alice.id,
            properties=PropertyFilterGroup.or_(
                {'since': 2015},
                {'since': 2020}
            )
        )

        assert len(results) == 2
        years = sorted([r.properties['since'] for r in results])
        assert years == [2015, 2020]
        db.close()

    def test_relationship_property_or_with_comparison(self):
        """Test OR with comparison operators on relationships."""
        db = GrafitoDatabase()
        alice = db.create_node(labels=['Person'], properties={'name': 'Alice'})
        company1 = db.create_node(labels=['Company'], properties={'name': 'Co1'})
        company2 = db.create_node(labels=['Company'], properties={'name': 'Co2'})
        company3 = db.create_node(labels=['Company'], properties={'name': 'Co3'})

        db.create_relationship(alice.id, company1.id, 'WORKS_AT', {'salary': 50000})
        db.create_relationship(alice.id, company2.id, 'WORKS_AT', {'salary': 75000})
        db.create_relationship(alice.id, company3.id, 'WORKS_AT', {'salary': 90000})

        # Salary < 60000 OR salary > 80000
        results = db.match_relationships(
            source_id=alice.id,
            properties=PropertyFilterGroup.or_(
                {'salary': PropertyFilter.lt(60000)},
                {'salary': PropertyFilter.gt(80000)}
            )
        )

        assert len(results) == 2
        salaries = sorted([r.properties['salary'] for r in results])
        assert salaries == [50000, 90000]
        db.close()


class TestOREdgeCases:
    """Test edge cases for OR logic."""

    def test_single_value_in_or_group(self):
        """Test OR with single value (still works)."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'city': 'NYC'})
        db.create_node(labels=['Person'], properties={'city': 'LA'})

        results = db.match_nodes(
            labels=['Person'],
            properties=PropertyFilterGroup.or_(
                {'city': 'NYC'}
            )
        )

        assert len(results) == 1
        db.close()

    def test_or_with_null_values(self):
        """Test OR logic with NULL values."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice', 'city': 'NYC'})
        db.create_node(labels=['Person'], properties={'name': 'Bob'})  # No city
        db.create_node(labels=['Person'], properties={'name': 'Charlie', 'city': 'LA'})

        # city=NYC OR city=NULL
        results = db.match_nodes(
            labels=['Person'],
            properties=PropertyFilterGroup.or_(
                {'city': 'NYC'},
                {'city': None}
            )
        )

        assert len(results) == 2
        names = sorted([n.properties['name'] for n in results])
        assert names == ['Alice', 'Bob']
        db.close()

    def test_or_all_conditions_match_same_node(self):
        """Test OR where same node matches multiple conditions."""
        db = GrafitoDatabase()
        # Node with city=NYC also has age=30
        db.create_node(labels=['Person'], properties={'city': 'NYC', 'age': 30})
        db.create_node(labels=['Person'], properties={'city': 'LA', 'age': 25})

        results = db.match_nodes(
            labels=['Person'],
            properties=PropertyFilterGroup.or_(
                {'city': 'NYC'},
                {'age': 30}
            )
        )

        # Should return 1 node (not duplicated)
        assert len(results) == 1
        db.close()

    def test_or_with_string_patterns(self):
        """Test OR with string pattern matching."""
        db = GrafitoDatabase()
        db.create_node(labels=['User'], properties={'email': 'alice@gmail.com'})
        db.create_node(labels=['User'], properties={'email': 'bob@yahoo.com'})
        db.create_node(labels=['User'], properties={'email': 'charlie@gmail.com'})
        db.create_node(labels=['User'], properties={'email': 'diana@hotmail.com'})

        results = db.match_nodes(
            labels=['User'],
            properties=PropertyFilterGroup.or_(
                {'email': PropertyFilter.ends_with('@gmail.com')},
                {'email': PropertyFilter.ends_with('@yahoo.com')}
            )
        )

        assert len(results) == 3
        db.close()
