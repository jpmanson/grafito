"""Tests for comparison operators in advanced filters."""

import pytest
from grafito import GrafitoDatabase, PropertyFilter, InvalidFilterError


class TestComparisonOperators:
    """Test comparison operators (>, <, >=, <=, !=, BETWEEN)."""

    def test_greater_than_integer(self):
        """Test > operator with integers."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 25})
        db.create_node(labels=['Person'], properties={'age': 30})
        db.create_node(labels=['Person'], properties={'age': 35})

        results = db.match_nodes(
            labels=['Person'],
            properties={'age': PropertyFilter.gt(30)}
        )

        assert len(results) == 1
        assert results[0].properties['age'] == 35
        db.close()

    def test_greater_than_float(self):
        """Test > operator with floats."""
        db = GrafitoDatabase()
        db.create_node(labels=['Product'], properties={'price': 19.99})
        db.create_node(labels=['Product'], properties={'price': 29.99})
        db.create_node(labels=['Product'], properties={'price': 39.99})

        results = db.match_nodes(
            labels=['Product'],
            properties={'price': PropertyFilter.gt(25.0)}
        )

        assert len(results) == 2
        db.close()

    def test_less_than_integer(self):
        """Test < operator with integers."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 25})
        db.create_node(labels=['Person'], properties={'age': 30})
        db.create_node(labels=['Person'], properties={'age': 35})

        results = db.match_nodes(
            labels=['Person'],
            properties={'age': PropertyFilter.lt(30)}
        )

        assert len(results) == 1
        assert results[0].properties['age'] == 25
        db.close()

    def test_greater_than_or_equal(self):
        """Test >= operator."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 25})
        db.create_node(labels=['Person'], properties={'age': 30})
        db.create_node(labels=['Person'], properties={'age': 35})

        results = db.match_nodes(
            labels=['Person'],
            properties={'age': PropertyFilter.gte(30)}
        )

        assert len(results) == 2
        ages = sorted([n.properties['age'] for n in results])
        assert ages == [30, 35]
        db.close()

    def test_less_than_or_equal(self):
        """Test <= operator."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 25})
        db.create_node(labels=['Person'], properties={'age': 30})
        db.create_node(labels=['Person'], properties={'age': 35})

        results = db.match_nodes(
            labels=['Person'],
            properties={'age': PropertyFilter.lte(30)}
        )

        assert len(results) == 2
        ages = sorted([n.properties['age'] for n in results])
        assert ages == [25, 30]
        db.close()

    def test_not_equal_string(self):
        """Test != operator with strings."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice'})
        db.create_node(labels=['Person'], properties={'name': 'Bob'})
        db.create_node(labels=['Person'], properties={'name': 'Charlie'})

        results = db.match_nodes(
            labels=['Person'],
            properties={'name': PropertyFilter.ne('Alice')}
        )

        assert len(results) == 2
        names = sorted([n.properties['name'] for n in results])
        assert names == ['Bob', 'Charlie']
        db.close()

    def test_not_equal_integer(self):
        """Test != operator with integers."""
        db = GrafitoDatabase()
        db.create_node(labels=['Item'], properties={'value': 10})
        db.create_node(labels=['Item'], properties={'value': 20})
        db.create_node(labels=['Item'], properties={'value': 30})

        results = db.match_nodes(
            labels=['Item'],
            properties={'value': PropertyFilter.ne(20)}
        )

        assert len(results) == 2
        values = sorted([n.properties['value'] for n in results])
        assert values == [10, 30]
        db.close()

    def test_between_inclusive(self):
        """Test BETWEEN operator (inclusive range)."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 20})
        db.create_node(labels=['Person'], properties={'age': 25})
        db.create_node(labels=['Person'], properties={'age': 30})
        db.create_node(labels=['Person'], properties={'age': 35})
        db.create_node(labels=['Person'], properties={'age': 40})

        results = db.match_nodes(
            labels=['Person'],
            properties={'age': PropertyFilter.between(25, 35)}
        )

        assert len(results) == 3
        ages = sorted([n.properties['age'] for n in results])
        assert ages == [25, 30, 35]
        db.close()

    def test_between_float_range(self):
        """Test BETWEEN with float range."""
        db = GrafitoDatabase()
        db.create_node(labels=['Product'], properties={'price': 9.99})
        db.create_node(labels=['Product'], properties={'price': 19.99})
        db.create_node(labels=['Product'], properties={'price': 29.99})
        db.create_node(labels=['Product'], properties={'price': 39.99})

        results = db.match_nodes(
            labels=['Product'],
            properties={'price': PropertyFilter.between(15.0, 35.0)}
        )

        assert len(results) == 2
        prices = sorted([n.properties['price'] for n in results])
        assert prices == [19.99, 29.99]
        db.close()

    def test_comparison_with_null_values(self):
        """Test comparison operators with NULL values."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice', 'age': 30})
        db.create_node(labels=['Person'], properties={'name': 'Bob'})  # No age
        db.create_node(labels=['Person'], properties={'name': 'Charlie', 'age': 25})

        # Greater than excludes NULLs
        results = db.match_nodes(
            labels=['Person'],
            properties={'age': PropertyFilter.gt(20)}
        )

        assert len(results) == 2
        names = sorted([n.properties['name'] for n in results])
        assert names == ['Alice', 'Charlie']
        db.close()

    def test_not_equal_includes_null(self):
        """Test != operator includes NULL values."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice', 'status': 'active'})
        db.create_node(labels=['Person'], properties={'name': 'Bob', 'status': 'inactive'})
        db.create_node(labels=['Person'], properties={'name': 'Charlie'})  # No status

        results = db.match_nodes(
            labels=['Person'],
            properties={'status': PropertyFilter.ne('active')}
        )

        # Should include both 'inactive' and NULL
        assert len(results) == 2
        names = sorted([n.properties['name'] for n in results])
        assert names == ['Bob', 'Charlie']
        db.close()

    def test_multiple_comparison_operators(self):
        """Test multiple comparison operators in one query."""
        db = GrafitoDatabase()
        db.create_node(labels=['Employee'], properties={'name': 'Alice', 'age': 25, 'salary': 50000})
        db.create_node(labels=['Employee'], properties={'name': 'Bob', 'age': 30, 'salary': 65000})
        db.create_node(labels=['Employee'], properties={'name': 'Charlie', 'age': 35, 'salary': 80000})
        db.create_node(labels=['Employee'], properties={'name': 'Diana', 'age': 28, 'salary': 55000})

        results = db.match_nodes(
            labels=['Employee'],
            properties={
                'age': PropertyFilter.gte(28),
                'salary': PropertyFilter.lt(70000)
            }
        )

        assert len(results) == 2
        names = sorted([n.properties['name'] for n in results])
        assert names == ['Bob', 'Diana']
        db.close()

    def test_comparison_with_exact_match(self):
        """Test mixing comparison operators with exact match."""
        db = GrafitoDatabase()
        db.create_node(labels=['Product'], properties={'category': 'Electronics', 'price': 100})
        db.create_node(labels=['Product'], properties={'category': 'Electronics', 'price': 200})
        db.create_node(labels=['Product'], properties={'category': 'Books', 'price': 150})
        db.create_node(labels=['Product'], properties={'category': 'Electronics', 'price': 300})

        results = db.match_nodes(
            labels=['Product'],
            properties={
                'category': 'Electronics',  # Exact match
                'price': PropertyFilter.between(150, 250)  # Range
            }
        )

        assert len(results) == 1
        assert results[0].properties['price'] == 200
        db.close()

    def test_comparison_on_relationships(self):
        """Test comparison operators on relationships."""
        db = GrafitoDatabase()
        alice = db.create_node(labels=['Person'], properties={'name': 'Alice'})
        bob = db.create_node(labels=['Person'], properties={'name': 'Bob'})
        charlie = db.create_node(labels=['Person'], properties={'name': 'Charlie'})
        company = db.create_node(labels=['Company'], properties={'name': 'TechCorp'})

        db.create_relationship(alice.id, company.id, 'WORKS_AT', {'since': 2018, 'salary': 50000})
        db.create_relationship(bob.id, company.id, 'WORKS_AT', {'since': 2020, 'salary': 65000})
        db.create_relationship(charlie.id, company.id, 'WORKS_AT', {'since': 2019, 'salary': 55000})

        results = db.match_relationships(
            rel_type='WORKS_AT',
            properties={'since': PropertyFilter.gte(2019)}
        )

        assert len(results) == 2
        years = sorted([r.properties['since'] for r in results])
        assert years == [2019, 2020]
        db.close()

    def test_comparison_string_ordering(self):
        """Test comparison operators with string values."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice'})
        db.create_node(labels=['Person'], properties={'name': 'Bob'})
        db.create_node(labels=['Person'], properties={'name': 'Charlie'})
        db.create_node(labels=['Person'], properties={'name': 'Diana'})

        # String comparison (alphabetical)
        results = db.match_nodes(
            labels=['Person'],
            properties={'name': PropertyFilter.gt('Bob')}
        )

        assert len(results) == 2
        names = sorted([n.properties['name'] for n in results])
        assert names == ['Charlie', 'Diana']
        db.close()

    def test_type_validation_success(self):
        """Test type validation passes for correct types."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 30})

        # This should work fine
        results = db.match_nodes(
            labels=['Person'],
            properties={'age': PropertyFilter.gt(25, expected_type=int)}
        )

        assert len(results) == 1
        db.close()

    def test_type_validation_failure(self):
        """Test type validation raises error for wrong types."""
        with pytest.raises(InvalidFilterError, match="Expected int, got str"):
            PropertyFilter.gt("30", expected_type=int)

    def test_between_validation(self):
        """Test BETWEEN validates both values."""
        with pytest.raises(InvalidFilterError):
            PropertyFilter.between(10, "20", expected_type=int)

    def test_comparison_zero_and_negative(self):
        """Test comparison with zero and negative numbers."""
        db = GrafitoDatabase()
        db.create_node(labels=['Account'], properties={'balance': -100})
        db.create_node(labels=['Account'], properties={'balance': 0})
        db.create_node(labels=['Account'], properties={'balance': 100})
        db.create_node(labels=['Account'], properties={'balance': 200})

        # Less than zero (negative balances)
        results = db.match_nodes(
            labels=['Account'],
            properties={'balance': PropertyFilter.lt(0)}
        )
        assert len(results) == 1
        assert results[0].properties['balance'] == -100

        # Greater than or equal to zero
        results = db.match_nodes(
            labels=['Account'],
            properties={'balance': PropertyFilter.gte(0)}
        )
        assert len(results) == 3
        db.close()

    def test_between_single_value(self):
        """Test BETWEEN with same min and max (equality)."""
        db = GrafitoDatabase()
        db.create_node(labels=['Item'], properties={'value': 10})
        db.create_node(labels=['Item'], properties={'value': 20})
        db.create_node(labels=['Item'], properties={'value': 30})

        results = db.match_nodes(
            labels=['Item'],
            properties={'value': PropertyFilter.between(20, 20)}
        )

        assert len(results) == 1
        assert results[0].properties['value'] == 20
        db.close()

    def test_comparison_empty_result(self):
        """Test comparison that yields no results."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 25})
        db.create_node(labels=['Person'], properties={'age': 30})

        results = db.match_nodes(
            labels=['Person'],
            properties={'age': PropertyFilter.gt(100)}
        )

        assert len(results) == 0
        db.close()

    def test_comparison_all_match(self):
        """Test comparison where all nodes match."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'age': 25})
        db.create_node(labels=['Person'], properties={'age': 30})
        db.create_node(labels=['Person'], properties={'age': 35})

        results = db.match_nodes(
            labels=['Person'],
            properties={'age': PropertyFilter.gt(20)}
        )

        assert len(results) == 3
        db.close()

    def test_not_equal_with_boolean(self):
        """Test != operator with boolean values."""
        db = GrafitoDatabase()
        db.create_node(labels=['User'], properties={'active': True})
        db.create_node(labels=['User'], properties={'active': False})
        db.create_node(labels=['User'], properties={'active': True})

        results = db.match_nodes(
            labels=['User'],
            properties={'active': PropertyFilter.ne(False)}
        )

        assert len(results) == 2
        db.close()
