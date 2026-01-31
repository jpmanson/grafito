"""Integration tests combining multiple advanced filter features."""

import pytest
from grafito import (
    GrafitoDatabase,
    PropertyFilter,
    PropertyFilterGroup,
    LabelFilter,
    SortOrder,
)


class TestEcommerceScenarios:
    """Test realistic e-commerce query scenarios."""

    def test_product_search_complex(self):
        """Test complex product search with multiple filters."""
        db = GrafitoDatabase()

        # Create products
        products_data = [
            ('Laptop Pro', 'Electronics', 1500, 4.8, True),
            ('Tablet Max', 'Electronics', 800, 4.5, True),
            ('Python Guide', 'Books', 45, 4.9, True),
            ('Phone Ultra', 'Electronics', 1200, 4.7, False),
            ('Graph Theory', 'Books', 55, 4.6, True),
            ('Smart Watch', 'Electronics', 400, 4.3, True),
            ('Mouse Pro', 'Electronics', 80, 4.8, True),
        ]

        for name, category, price, rating, in_stock in products_data:
            db.create_node(
                labels=['Product', category],
                properties={
                    'name': name,
                    'price': price,
                    'rating': rating,
                    'in_stock': in_stock
                }
            )

        # Search: Electronics OR Books, price 40-1000, rating >= 4.5,
        # in stock, sorted by rating DESC, limit 3
        results = db.match_nodes(
            labels=LabelFilter.any(['Electronics', 'Books']),
            properties={
                'price': PropertyFilter.between(40, 1000),
                'rating': PropertyFilter.gte(4.5),
                'in_stock': True
            },
            order_by='rating',
            ascending=False,
            limit=3
        )

        assert len(results) == 3
        # Should be: Python Guide (4.9), Mouse Pro (4.8), Graph Theory (4.6)
        ratings = [n.properties['rating'] for n in results]
        assert ratings == [4.9, 4.8, 4.6]

        # Verify price filter worked
        for node in results:
            assert 40 <= node.properties['price'] <= 1000

        db.close()

    def test_product_search_with_name_filter(self):
        """Test product search with string matching."""
        db = GrafitoDatabase()

        products = [
            ('Wireless Mouse', 'Electronics', 25),
            ('Gaming Mouse Pro', 'Electronics', 80),
            ('Keyboard Wireless', 'Electronics', 60),
            ('Mouse Pad', 'Accessories', 15),
        ]

        for name, category, price in products:
            db.create_node(
                labels=['Product'],
                properties={'name': name, 'category': category, 'price': price}
            )

        # Find products with "Mouse" in name, Electronics category, sorted by price
        results = db.match_nodes(
            labels=['Product'],
            properties={
                'name': PropertyFilter.contains('Mouse', case_sensitive=False),
                'category': 'Electronics'
            },
            order_by='price',
            ascending=True
        )

        assert len(results) == 2
        names = [n.properties['name'] for n in results]
        assert names == ['Wireless Mouse', 'Gaming Mouse Pro']
        db.close()


class TestSocialNetworkScenarios:
    """Test social network query scenarios."""

    def test_friend_recommendations(self):
        """Test finding potential friends based on criteria."""
        db = GrafitoDatabase()

        # Create users
        users_data = [
            ('Alice', 'NYC', 30, ['Python', 'Graphs']),
            ('Bob', 'NYC', 28, ['Python', 'AI']),
            ('Charlie', 'LA', 30, ['Java', 'Web']),
            ('Diana', 'NYC', 32, ['Python', 'Web']),
            ('Eve', 'SF', 29, ['Python', 'Graphs']),
        ]

        for name, city, age, interests in users_data:
            db.create_node(
                labels=['Person'],
                properties={
                    'name': name,
                    'city': city,
                    'age': age,
                    'interests': interests
                }
            )

        my_age = 30
        my_city = 'NYC'

        # Find potential friends: same city OR age within 3 years
        results = db.match_nodes(
            labels=['Person'],
            properties=PropertyFilterGroup.or_(
                {'city': my_city},
                {'age': PropertyFilter.between(my_age - 3, my_age + 3)}
            ),
            order_by='age'
        )

        # Should exclude only Eve (SF, age 29 - wrong city and age outside range)
        assert len(results) >= 4
        cities = [n.properties['city'] for n in results]
        ages = [n.properties['age'] for n in results]

        # Verify all match criteria
        for city, age in zip(cities, ages):
            assert city == my_city or (my_age - 3 <= age <= my_age + 3)

        db.close()

    def test_relationship_strength_analysis(self):
        """Test analyzing relationship strength with filters."""
        db = GrafitoDatabase()

        alice = db.create_node(labels=['Person'], properties={'name': 'Alice'})

        # Create friendships with varying strength
        friends_data = [
            ('Bob', 2018, 9),      # Old friend, high closeness
            ('Charlie', 2020, 7),  # Recent friend, medium closeness
            ('Diana', 2015, 10),   # Very old friend, highest closeness
            ('Eve', 2021, 5),      # New friend, low closeness
            ('Frank', 2019, 8),    # Medium age, high closeness
        ]

        for name, since, closeness in friends_data:
            friend = db.create_node(labels=['Person'], properties={'name': name})
            db.create_relationship(
                alice.id, friend.id, 'FRIENDS_WITH',
                {'since': since, 'closeness': closeness}
            )

        # Find close friendships (closeness > 7) from 2018 or earlier
        results = db.match_relationships(
            source_id=alice.id,
            rel_type='FRIENDS_WITH',
            properties={
                'closeness': PropertyFilter.gt(7),
                'since': PropertyFilter.lte(2018)
            },
            order_by='closeness',
            ascending=False
        )

        assert len(results) == 2  # Diana and Bob
        closeness_values = [r.properties['closeness'] for r in results]
        assert closeness_values == [10, 9]
        db.close()


class TestEmployeeManagementScenarios:
    """Test employee management query scenarios."""

    def test_salary_analysis(self):
        """Test complex salary-based queries."""
        db = GrafitoDatabase()

        employees_data = [
            ('Alice', 'Engineering', 90000, 5, 'Senior'),
            ('Bob', 'Engineering', 75000, 3, 'Mid'),
            ('Charlie', 'Sales', 65000, 4, 'Mid'),
            ('Diana', 'Engineering', 110000, 8, 'Lead'),
            ('Eve', 'Sales', 70000, 6, 'Senior'),
            ('Frank', 'HR', 60000, 3, 'Mid'),
        ]

        for name, dept, salary, years, level in employees_data:
            db.create_node(
                labels=['Employee'],
                properties={
                    'name': name,
                    'department': dept,
                    'salary': salary,
                    'years_experience': years,
                    'level': level
                }
            )

        # Find mid-to-high earners in Engineering or Sales
        # Salary >= 70000, sorted by salary DESC
        results = db.match_nodes(
            labels=['Employee'],
            properties=PropertyFilterGroup.and_(
                {'salary': PropertyFilter.gte(70000)},
                PropertyFilterGroup.or_(
                    {'department': 'Engineering'},
                    {'department': 'Sales'}
                )
            ),
            order_by='salary',
            ascending=False,
            limit=5
        )

        assert len(results) == 4
        # Diana, Alice, Bob, Eve
        salaries = [n.properties['salary'] for n in results]
        assert salaries == [110000, 90000, 75000, 70000]
        db.close()

    def test_promotion_candidates(self):
        """Test finding promotion candidates."""
        db = GrafitoDatabase()

        employees_data = [
            ('Alice', 85000, 4, 'Mid', 4.5),
            ('Bob', 75000, 2, 'Junior', 4.2),
            ('Charlie', 90000, 6, 'Senior', 4.8),
            ('Diana', 80000, 5, 'Mid', 4.7),
            ('Eve', 78000, 3, 'Mid', 4.3),
        ]

        for name, salary, years, level, rating in employees_data:
            db.create_node(
                labels=['Employee'],
                properties={
                    'name': name,
                    'salary': salary,
                    'years_experience': years,
                    'level': level,
                    'performance_rating': rating
                }
            )

        # Mid-level employees with 3+ years and rating >= 4.5
        results = db.match_nodes(
            labels=['Employee'],
            properties={
                'level': 'Mid',
                'years_experience': PropertyFilter.gte(3),
                'performance_rating': PropertyFilter.gte(4.5)
            },
            order_by='performance_rating',
            ascending=False
        )

        assert len(results) == 2  # Alice and Diana
        names = [n.properties['name'] for n in results]
        assert set(names) == {'Alice', 'Diana'}
        db.close()


class TestComplexCombinations:
    """Test complex combinations of multiple features."""

    def test_all_features_combined(self):
        """Test combining all advanced features in one query."""
        db = GrafitoDatabase()

        # Create diverse dataset
        for i in range(50):
            db.create_node(
                labels=['Item'],
                properties={
                    'code': f'ITEM{i:03d}',
                    'category': 'A' if i % 3 == 0 else 'B' if i % 3 == 1 else 'C',
                    'value': i * 10,
                    'active': i % 2 == 0,
                    'name': f'Item {i}'
                }
            )

        # Complex query:
        # - code starts with "ITEM0" OR "ITEM1"
        # - category = A or B
        # - value between 100 and 300
        # - active = true
        # - order by value DESC
        # - limit 5, offset 2
        results = db.match_nodes(
            labels=['Item'],
            properties=PropertyFilterGroup.and_(
                PropertyFilterGroup.or_(
                    {'code': PropertyFilter.starts_with('ITEM0')},
                    {'code': PropertyFilter.starts_with('ITEM1')}
                ),
                PropertyFilterGroup.or_(
                    {'category': 'A'},
                    {'category': 'B'}
                ),
                {'value': PropertyFilter.between(100, 300)},
                {'active': True}
            ),
            order_by='value',
            ascending=False,
            limit=5,
            offset=2
        )

        # Verify results meet all criteria
        for node in results:
            props = node.properties
            assert props['code'].startswith('ITEM0') or props['code'].startswith('ITEM1')
            assert props['category'] in ('A', 'B')
            assert 100 <= props['value'] <= 300
            assert props['active'] is True

        assert len(results) <= 5
        db.close()

    def test_pagination_across_filtered_results(self):
        """Test that pagination works correctly with heavy filtering."""
        db = GrafitoDatabase()

        # Create 100 items
        for i in range(100):
            db.create_node(
                labels=['Item'],
                properties={
                    'number': i,
                    'even': i % 2 == 0,
                    'divisible_by_5': i % 5 == 0
                }
            )

        # Filter: even AND divisible by 5 (i.e., divisible by 10)
        # Should have 10 results: 0, 10, 20, ..., 90

        # Get page 1 (first 3)
        page1 = db.match_nodes(
            labels=['Item'],
            properties={
                'even': True,
                'divisible_by_5': True
            },
            order_by='number',
            limit=3,
            offset=0
        )
        assert len(page1) == 3
        assert [n.properties['number'] for n in page1] == [0, 10, 20]

        # Get page 2 (next 3)
        page2 = db.match_nodes(
            labels=['Item'],
            properties={
                'even': True,
                'divisible_by_5': True
            },
            order_by='number',
            limit=3,
            offset=3
        )
        assert len(page2) == 3
        assert [n.properties['number'] for n in page2] == [30, 40, 50]

        db.close()


class TestBackwardCompatibility:
    """Test that new features don't break existing functionality."""

    def test_old_api_still_works(self):
        """Test that all old API calls work unchanged."""
        db = GrafitoDatabase()

        # Old API: exact matches
        alice = db.create_node(labels=['Person'], properties={'name': 'Alice', 'age': 30})
        bob = db.create_node(labels=['Person', 'Employee'], properties={'name': 'Bob', 'age': 25})
        company = db.create_node(labels=['Company'], properties={'name': 'TechCorp'})

        # Old API: match by labels
        persons = db.match_nodes(labels=['Person'])
        assert len(persons) == 2

        # Old API: match by labels + properties
        employees = db.match_nodes(labels=['Person', 'Employee'], properties={'name': 'Bob'})
        assert len(employees) == 1
        assert employees[0].properties['name'] == 'Bob'

        # Old API: match relationships
        rel = db.create_relationship(bob.id, company.id, 'WORKS_AT', {'since': 2020})
        rels = db.match_relationships(source_id=bob.id, rel_type='WORKS_AT')
        assert len(rels) == 1
        assert rels[0].properties['since'] == 2020

        db.close()

    def test_mixing_old_and_new_api(self):
        """Test mixing old and new API styles."""
        db = GrafitoDatabase()

        # Create with old API
        for i in range(10):
            db.create_node(labels=['Item'], properties={'value': i, 'category': 'A'})

        # Query with new API
        results = db.match_nodes(
            labels=['Item'],  # Old style: plain list
            properties={'value': PropertyFilter.gte(5)},  # New style: PropertyFilter
            order_by='value',  # New style: ordering
            limit=3  # New style: pagination
        )

        assert len(results) == 3
        values = [n.properties['value'] for n in results]
        assert values == [5, 6, 7]

        db.close()

    def test_empty_filters_still_work(self):
        """Test that empty or None filters work as before."""
        db = GrafitoDatabase()

        db.create_node(labels=['A'], properties={'x': 1})
        db.create_node(labels=['B'], properties={'y': 2})

        # No filters - should return all
        results = db.match_nodes()
        assert len(results) == 2

        # None labels - should return all
        results = db.match_nodes(labels=None)
        assert len(results) == 2

        # Empty properties - should return all matching label
        results = db.match_nodes(labels=['A'], properties={})
        assert len(results) == 1

        db.close()


class TestPerformanceConsiderations:
    """Test queries that might have performance implications."""

    def test_large_result_set_with_ordering(self):
        """Test ordering large result sets."""
        db = GrafitoDatabase()

        # Create 1000 nodes
        for i in range(1000):
            db.create_node(
                labels=['Item'],
                properties={'value': i % 100, 'category': f'Cat{i % 10}'}
            )

        # Order by value (many duplicates)
        results = db.match_nodes(
            labels=['Item'],
            order_by='value',
            limit=50
        )

        assert len(results) == 50
        # Verify ordering
        values = [n.properties['value'] for n in results]
        assert values == sorted(values)

        db.close()

    def test_deep_pagination(self):
        """Test pagination with large offset."""
        db = GrafitoDatabase()

        # Create 500 nodes
        for i in range(500):
            db.create_node(labels=['Item'], properties={'number': i})

        # Get results at offset 450
        results = db.match_nodes(
            labels=['Item'],
            order_by='number',
            limit=10,
            offset=450
        )

        assert len(results) == 10
        numbers = [n.properties['number'] for n in results]
        assert numbers == list(range(450, 460))

        db.close()
