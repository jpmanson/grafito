"""Tests for ordering and pagination in advanced filters."""

import pytest
from grafito import GrafitoDatabase, PropertyFilter, SortOrder, InvalidFilterError


class TestOrdering:
    """Test ordering functionality."""

    def test_order_by_single_property_ascending(self):
        """Test ordering by single property in ascending order."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Charlie', 'age': 35})
        db.create_node(labels=['Person'], properties={'name': 'Alice', 'age': 25})
        db.create_node(labels=['Person'], properties={'name': 'Bob', 'age': 30})

        results = db.match_nodes(
            labels=['Person'],
            order_by='age',
            ascending=True
        )

        ages = [n.properties['age'] for n in results]
        assert ages == [25, 30, 35]
        db.close()

    def test_order_by_single_property_descending(self):
        """Test ordering by single property in descending order."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Charlie', 'age': 35})
        db.create_node(labels=['Person'], properties={'name': 'Alice', 'age': 25})
        db.create_node(labels=['Person'], properties={'name': 'Bob', 'age': 30})

        results = db.match_nodes(
            labels=['Person'],
            order_by='age',
            ascending=False
        )

        ages = [n.properties['age'] for n in results]
        assert ages == [35, 30, 25]
        db.close()

    def test_order_by_string_property(self):
        """Test ordering by string property (alphabetical)."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Charlie'})
        db.create_node(labels=['Person'], properties={'name': 'Alice'})
        db.create_node(labels=['Person'], properties={'name': 'Bob'})

        results = db.match_nodes(
            labels=['Person'],
            order_by='name',
            ascending=True
        )

        names = [n.properties['name'] for n in results]
        assert names == ['Alice', 'Bob', 'Charlie']
        db.close()

    def test_order_by_float_property(self):
        """Test ordering by float property."""
        db = GrafitoDatabase()
        db.create_node(labels=['Product'], properties={'price': 29.99})
        db.create_node(labels=['Product'], properties={'price': 9.99})
        db.create_node(labels=['Product'], properties={'price': 19.99})

        results = db.match_nodes(
            labels=['Product'],
            order_by='price',
            ascending=True
        )

        prices = [n.properties['price'] for n in results]
        assert prices == [9.99, 19.99, 29.99]
        db.close()

    def test_order_by_multiple_properties_same_direction(self):
        """Test ordering by multiple properties with same direction."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'city': 'NYC', 'age': 30})
        db.create_node(labels=['Person'], properties={'city': 'LA', 'age': 25})
        db.create_node(labels=['Person'], properties={'city': 'NYC', 'age': 25})
        db.create_node(labels=['Person'], properties={'city': 'LA', 'age': 30})

        results = db.match_nodes(
            labels=['Person'],
            order_by=['city', 'age'],
            ascending=True
        )

        cities_ages = [(n.properties['city'], n.properties['age']) for n in results]
        # Should order by city first, then age
        assert cities_ages == [('LA', 25), ('LA', 30), ('NYC', 25), ('NYC', 30)]
        db.close()

    def test_order_by_sort_order_objects(self):
        """Test ordering with SortOrder objects for mixed directions."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'city': 'NYC', 'age': 30})
        db.create_node(labels=['Person'], properties={'city': 'LA', 'age': 25})
        db.create_node(labels=['Person'], properties={'city': 'NYC', 'age': 25})
        db.create_node(labels=['Person'], properties={'city': 'LA', 'age': 30})

        results = db.match_nodes(
            labels=['Person'],
            order_by=[
                SortOrder('city', ascending=True),
                SortOrder('age', ascending=False)
            ]
        )

        cities_ages = [(n.properties['city'], n.properties['age']) for n in results]
        # City ASC, age DESC
        assert cities_ages == [('LA', 30), ('LA', 25), ('NYC', 30), ('NYC', 25)]
        db.close()

    def test_order_by_with_filters(self):
        """Test ordering combined with property filters."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 20, 'name': 'Eve'})
        db.create_node(labels=['Person'], properties={'age': 30, 'name': 'Charlie'})
        db.create_node(labels=['Person'], properties={'age': 40, 'name': 'Alice'})
        db.create_node(labels=['Person'], properties={'age': 35, 'name': 'Bob'})
        db.create_node(labels=['Person'], properties={'age': 45, 'name': 'Diana'})

        results = db.match_nodes(
            labels=['Person'],
            properties={'age': PropertyFilter.between(25, 40)},
            order_by='name',
            ascending=True
        )

        names = [n.properties['name'] for n in results]
        assert names == ['Alice', 'Bob', 'Charlie']
        db.close()

    def test_order_by_null_values(self):
        """Test ordering with NULL values (NULLs are placed last by default)."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice', 'age': 30})
        db.create_node(labels=['Person'], properties={'name': 'Bob'})  # No age
        db.create_node(labels=['Person'], properties={'name': 'Charlie', 'age': 25})

        results = db.match_nodes(
            labels=['Person'],
            order_by='age',
            ascending=True
        )

        # NULLs are placed last in ordering
        ages = [n.properties.get('age') for n in results]
        assert ages == [25, 30, None]
        db.close()

    def test_order_by_relationships(self):
        """Test ordering on relationships."""
        db = GrafitoDatabase()
        alice = db.create_node(labels=['Person'], properties={'name': 'Alice'})
        company1 = db.create_node(labels=['Company'], properties={'name': 'Co1'})
        company2 = db.create_node(labels=['Company'], properties={'name': 'Co2'})
        company3 = db.create_node(labels=['Company'], properties={'name': 'Co3'})

        db.create_relationship(alice.id, company1.id, 'WORKS_AT', {'since': 2020})
        db.create_relationship(alice.id, company2.id, 'APPLIED_TO', {'since': 2018})
        db.create_relationship(alice.id, company3.id, 'WORKS_AT', {'since': 2019})

        results = db.match_relationships(
            source_id=alice.id,
            rel_type='WORKS_AT',
            order_by='since',
            ascending=True
        )

        years = [r.properties['since'] for r in results]
        assert years == [2019, 2020]
        db.close()

    def test_order_without_filters_returns_all(self):
        """Test ordering without filters returns all nodes."""
        db = GrafitoDatabase()
        db.create_node(labels=['Item'], properties={'value': 3})
        db.create_node(labels=['Item'], properties={'value': 1})
        db.create_node(labels=['Item'], properties={'value': 2})

        results = db.match_nodes(
            labels=['Item'],
            order_by='value'
        )

        assert len(results) == 3
        values = [n.properties['value'] for n in results]
        assert values == [1, 2, 3]
        db.close()

    def test_order_by_invalid_property_name(self):
        """Test ordering with invalid property name raises error."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 30})

        with pytest.raises(InvalidFilterError, match="Invalid property name"):
            db.match_nodes(
                labels=['Person'],
                order_by='age; DROP TABLE nodes--'
            )
        db.close()


class TestPagination:
    """Test pagination functionality."""

    def test_limit_only(self):
        """Test LIMIT without OFFSET."""
        db = GrafitoDatabase()
        for i in range(10):
            db.create_node(labels=['Item'], properties={'number': i})

        results = db.match_nodes(
            labels=['Item'],
            order_by='number',
            limit=5
        )

        assert len(results) == 5
        numbers = [n.properties['number'] for n in results]
        assert numbers == [0, 1, 2, 3, 4]
        db.close()

    def test_limit_with_offset(self):
        """Test LIMIT with OFFSET (pagination)."""
        db = GrafitoDatabase()
        for i in range(10):
            db.create_node(labels=['Item'], properties={'number': i})

        # Page 2 (skip first 5, take next 5)
        results = db.match_nodes(
            labels=['Item'],
            order_by='number',
            limit=5,
            offset=5
        )

        assert len(results) == 5
        numbers = [n.properties['number'] for n in results]
        assert numbers == [5, 6, 7, 8, 9]
        db.close()

    def test_offset_beyond_result_set(self):
        """Test OFFSET beyond available results."""
        db = GrafitoDatabase()
        for i in range(5):
            db.create_node(labels=['Item'], properties={'number': i})

        results = db.match_nodes(
            labels=['Item'],
            order_by='number',
            limit=5,
            offset=10
        )

        assert len(results) == 0
        db.close()

    def test_pagination_multiple_pages(self):
        """Test paginating through multiple pages."""
        db = GrafitoDatabase()
        for i in range(20):
            db.create_node(labels=['Item'], properties={'number': i})

        # Page 1
        page1 = db.match_nodes(
            labels=['Item'],
            order_by='number',
            limit=5,
            offset=0
        )
        assert len(page1) == 5
        assert [n.properties['number'] for n in page1] == [0, 1, 2, 3, 4]

        # Page 2
        page2 = db.match_nodes(
            labels=['Item'],
            order_by='number',
            limit=5,
            offset=5
        )
        assert len(page2) == 5
        assert [n.properties['number'] for n in page2] == [5, 6, 7, 8, 9]

        # Page 3
        page3 = db.match_nodes(
            labels=['Item'],
            order_by='number',
            limit=5,
            offset=10
        )
        assert len(page3) == 5
        assert [n.properties['number'] for n in page3] == [10, 11, 12, 13, 14]
        db.close()

    def test_limit_larger_than_result_set(self):
        """Test LIMIT larger than available results."""
        db = GrafitoDatabase()
        for i in range(5):
            db.create_node(labels=['Item'], properties={'number': i})

        results = db.match_nodes(
            labels=['Item'],
            order_by='number',
            limit=100
        )

        assert len(results) == 5
        db.close()

    def test_limit_zero(self):
        """Test LIMIT of 0 returns empty result."""
        db = GrafitoDatabase()
        for i in range(5):
            db.create_node(labels=['Item'], properties={'number': i})

        results = db.match_nodes(
            labels=['Item'],
            limit=0
        )

        assert len(results) == 0
        db.close()

    def test_limit_negative_raises_error(self):
        """Test negative LIMIT raises error."""
        db = GrafitoDatabase()
        db.create_node(labels=['Item'], properties={'number': 1})

        with pytest.raises(InvalidFilterError, match="Limit must be non-negative"):
            db.match_nodes(labels=['Item'], limit=-1)
        db.close()

    def test_offset_negative_raises_error(self):
        """Test negative OFFSET raises error."""
        db = GrafitoDatabase()
        db.create_node(labels=['Item'], properties={'number': 1})

        with pytest.raises(InvalidFilterError, match="Offset must be non-negative"):
            db.match_nodes(labels=['Item'], limit=5, offset=-1)
        db.close()

    def test_pagination_with_filters(self):
        """Test pagination combined with filters."""
        db = GrafitoDatabase()
        for i in range(20):
            db.create_node(labels=['Item'], properties={'number': i, 'even': i % 2 == 0})

        # Get first 5 even numbers
        results = db.match_nodes(
            labels=['Item'],
            properties={'even': True},
            order_by='number',
            limit=5,
            offset=0
        )

        assert len(results) == 5
        numbers = [n.properties['number'] for n in results]
        assert numbers == [0, 2, 4, 6, 8]
        db.close()

    def test_pagination_on_relationships(self):
        """Test pagination on relationships."""
        db = GrafitoDatabase()
        alice = db.create_node(labels=['Person'], properties={'name': 'Alice'})

        for i in range(10):
            company = db.create_node(labels=['Company'], properties={'name': f'Co{i}'})
            db.create_relationship(alice.id, company.id, 'APPLIED_TO', {'year': 2020 + i})

        results = db.match_relationships(
            source_id=alice.id,
            order_by='year',
            limit=3,
            offset=2
        )

        assert len(results) == 3
        years = [r.properties['year'] for r in results]
        assert years == [2022, 2023, 2024]
        db.close()


class TestOrderingAndPaginationCombined:
    """Test combining ordering and pagination."""

    def test_order_then_paginate(self):
        """Test that ordering happens before pagination."""
        db = GrafitoDatabase()
        # Create nodes in random order
        values = [5, 2, 8, 1, 9, 3, 7, 4, 6, 0]
        for v in values:
            db.create_node(labels=['Item'], properties={'value': v})

        # Get middle 3 when sorted
        results = db.match_nodes(
            labels=['Item'],
            order_by='value',
            ascending=True,
            limit=3,
            offset=3
        )

        assert len(results) == 3
        sorted_values = [n.properties['value'] for n in results]
        assert sorted_values == [3, 4, 5]
        db.close()

    def test_descending_order_with_pagination(self):
        """Test descending order with pagination."""
        db = GrafitoDatabase()
        for i in range(10):
            db.create_node(labels=['Item'], properties={'value': i})

        # Get top 3 highest values
        results = db.match_nodes(
            labels=['Item'],
            order_by='value',
            ascending=False,
            limit=3
        )

        assert len(results) == 3
        values = [n.properties['value'] for n in results]
        assert values == [9, 8, 7]
        db.close()

    def test_multi_property_order_with_pagination(self):
        """Test multi-property ordering with pagination."""
        db = GrafitoDatabase()
        # Create data with duplicate categories
        data = [
            ('A', 3), ('A', 1), ('A', 2),
            ('B', 2), ('B', 1), ('B', 3),
            ('C', 1), ('C', 3), ('C', 2)
        ]
        for category, value in data:
            db.create_node(labels=['Item'], properties={'category': category, 'value': value})

        # Get second page when ordering by category then value
        results = db.match_nodes(
            labels=['Item'],
            order_by=['category', 'value'],
            ascending=True,
            limit=3,
            offset=3
        )

        assert len(results) == 3
        pairs = [(n.properties['category'], n.properties['value']) for n in results]
        assert pairs == [('B', 1), ('B', 2), ('B', 3)]
        db.close()

    def test_pagination_preserves_order(self):
        """Test that pagination preserves sort order across pages."""
        db = GrafitoDatabase()
        for i in range(15):
            db.create_node(labels=['Item'], properties={'value': i})

        # Get all items across 3 pages
        all_results = []
        for page in range(3):
            page_results = db.match_nodes(
                labels=['Item'],
                order_by='value',
                ascending=True,
                limit=5,
                offset=page * 5
            )
            all_results.extend([n.properties['value'] for n in page_results])

        # Should have all values in order
        assert all_results == list(range(15))
        db.close()

    def test_sort_order_object_repr(self):
        """Test SortOrder __repr__ method."""
        sort_asc = SortOrder('age', ascending=True)
        assert 'age' in repr(sort_asc)
        assert 'ASC' in repr(sort_asc)

        sort_desc = SortOrder('name', ascending=False)
        assert 'name' in repr(sort_desc)
        assert 'DESC' in repr(sort_desc)

    def test_sort_order_empty_property_raises_error(self):
        """Test SortOrder with empty property name raises error."""
        with pytest.raises(InvalidFilterError, match="property name cannot be empty"):
            SortOrder('')
