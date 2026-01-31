"""Tests for string pattern matching in advanced filters."""

import pytest
from grafito import GrafitoDatabase, PropertyFilter, InvalidFilterError


class TestStringMatching:
    """Test string pattern matching (CONTAINS, STARTS_WITH, ENDS_WITH, REGEX)."""

    def test_contains_case_sensitive(self):
        """Test CONTAINS with case-sensitive matching."""
        db = GrafitoDatabase()
        db.create_node(labels=['User'], properties={'name': 'Alice Johnson'})
        db.create_node(labels=['User'], properties={'name': 'Bob Smith'})
        db.create_node(labels=['User'], properties={'name': 'Charlie Brown'})

        results = db.match_nodes(
            labels=['User'],
            properties={'name': PropertyFilter.contains('Alice', case_sensitive=True)}
        )

        assert len(results) == 1
        assert results[0].properties['name'] == 'Alice Johnson'
        db.close()

    def test_contains_case_insensitive(self):
        """Test CONTAINS with case-insensitive matching."""
        db = GrafitoDatabase()
        db.create_node(labels=['User'], properties={'name': 'Alice Johnson'})
        db.create_node(labels=['User'], properties={'name': 'Bob Smith'})
        db.create_node(labels=['User'], properties={'name': 'Charlie Brown'})

        results = db.match_nodes(
            labels=['User'],
            properties={'name': PropertyFilter.contains('alice', case_sensitive=False)}
        )

        assert len(results) == 1
        assert results[0].properties['name'] == 'Alice Johnson'
        db.close()

    def test_contains_middle_of_string(self):
        """Test CONTAINS finds substring in middle."""
        db = GrafitoDatabase()
        db.create_node(labels=['Product'], properties={'name': 'Laptop Computer'})
        db.create_node(labels=['Product'], properties={'name': 'Desktop Computer'})
        db.create_node(labels=['Product'], properties={'name': 'Tablet Device'})

        results = db.match_nodes(
            labels=['Product'],
            properties={'name': PropertyFilter.contains('Computer')}
        )

        assert len(results) == 2
        db.close()

    def test_contains_at_start(self):
        """Test CONTAINS finds substring at start."""
        db = GrafitoDatabase()
        db.create_node(labels=['User'], properties={'email': 'alice@example.com'})
        db.create_node(labels=['User'], properties={'email': 'bob@example.com'})
        db.create_node(labels=['User'], properties={'email': 'charlie@gmail.com'})

        results = db.match_nodes(
            labels=['User'],
            properties={'email': PropertyFilter.contains('alice')}
        )

        assert len(results) == 1
        db.close()

    def test_contains_at_end(self):
        """Test CONTAINS finds substring at end."""
        db = GrafitoDatabase()
        db.create_node(labels=['File'], properties={'name': 'document.pdf'})
        db.create_node(labels=['File'], properties={'name': 'image.png'})
        db.create_node(labels=['File'], properties={'name': 'report.pdf'})

        results = db.match_nodes(
            labels=['File'],
            properties={'name': PropertyFilter.contains('.pdf')}
        )

        assert len(results) == 2
        db.close()

    def test_starts_with_case_sensitive(self):
        """Test STARTS_WITH with case-sensitive matching."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice'})
        db.create_node(labels=['Person'], properties={'name': 'alice'})
        db.create_node(labels=['Person'], properties={'name': 'Bob'})

        results = db.match_nodes(
            labels=['Person'],
            properties={'name': PropertyFilter.starts_with('A', case_sensitive=True)}
        )

        assert len(results) == 1
        assert results[0].properties['name'] == 'Alice'
        db.close()

    def test_starts_with_case_insensitive(self):
        """Test STARTS_WITH with case-insensitive matching."""
        db = GrafitoDatabase()
        db.create_node(labels=['Person'], properties={'name': 'Alice'})
        db.create_node(labels=['Person'], properties={'name': 'alice'})
        db.create_node(labels=['Person'], properties={'name': 'Bob'})

        results = db.match_nodes(
            labels=['Person'],
            properties={'name': PropertyFilter.starts_with('a', case_sensitive=False)}
        )

        assert len(results) == 2
        db.close()

    def test_starts_with_multiple_chars(self):
        """Test STARTS_WITH with multiple characters."""
        db = GrafitoDatabase()
        db.create_node(labels=['User'], properties={'email': 'john.doe@example.com'})
        db.create_node(labels=['User'], properties={'email': 'john.smith@example.com'})
        db.create_node(labels=['User'], properties={'email': 'jane.doe@example.com'})

        results = db.match_nodes(
            labels=['User'],
            properties={'email': PropertyFilter.starts_with('john')}
        )

        assert len(results) == 2
        db.close()

    def test_ends_with_case_sensitive(self):
        """Test ENDS_WITH with case-sensitive matching."""
        db = GrafitoDatabase()
        db.create_node(labels=['User'], properties={'email': 'alice@GMAIL.COM'})
        db.create_node(labels=['User'], properties={'email': 'bob@gmail.com'})
        db.create_node(labels=['User'], properties={'email': 'charlie@yahoo.com'})

        results = db.match_nodes(
            labels=['User'],
            properties={'email': PropertyFilter.ends_with('gmail.com', case_sensitive=True)}
        )

        assert len(results) == 1
        assert results[0].properties['email'] == 'bob@gmail.com'
        db.close()

    def test_ends_with_case_insensitive(self):
        """Test ENDS_WITH with case-insensitive matching."""
        db = GrafitoDatabase()
        db.create_node(labels=['User'], properties={'email': 'alice@GMAIL.COM'})
        db.create_node(labels=['User'], properties={'email': 'bob@gmail.com'})
        db.create_node(labels=['User'], properties={'email': 'charlie@yahoo.com'})

        results = db.match_nodes(
            labels=['User'],
            properties={'email': PropertyFilter.ends_with('gmail.com', case_sensitive=False)}
        )

        assert len(results) == 2
        db.close()

    def test_ends_with_extension(self):
        """Test ENDS_WITH for file extensions."""
        db = GrafitoDatabase()
        db.create_node(labels=['File'], properties={'name': 'document.txt'})
        db.create_node(labels=['File'], properties={'name': 'image.jpg'})
        db.create_node(labels=['File'], properties={'name': 'report.txt'})
        db.create_node(labels=['File'], properties={'name': 'photo.png'})

        results = db.match_nodes(
            labels=['File'],
            properties={'name': PropertyFilter.ends_with('.txt')}
        )

        assert len(results) == 2
        db.close()

    def test_regex_simple_pattern(self):
        """Test REGEX with simple pattern."""
        db = GrafitoDatabase()
        db.create_node(labels=['User'], properties={'email': 'alice@example.com'})
        db.create_node(labels=['User'], properties={'email': 'bob@example.com'})
        db.create_node(labels=['User'], properties={'email': 'charlie@gmail.com'})

        results = db.match_nodes(
            labels=['User'],
            properties={'email': PropertyFilter.regex(r'.*@example\.com')}
        )

        assert len(results) == 2
        db.close()

    def test_regex_phone_pattern(self):
        """Test REGEX with phone number pattern."""
        db = GrafitoDatabase()
        db.create_node(labels=['Contact'], properties={'phone': '123-456-7890'})
        db.create_node(labels=['Contact'], properties={'phone': '987-654-3210'})
        db.create_node(labels=['Contact'], properties={'phone': '555-1234'})  # Invalid format

        results = db.match_nodes(
            labels=['Contact'],
            properties={'phone': PropertyFilter.regex(r'^\d{3}-\d{3}-\d{4}$')}
        )

        assert len(results) == 2
        db.close()

    def test_regex_digit_pattern(self):
        """Test REGEX with digit patterns."""
        db = GrafitoDatabase()
        db.create_node(labels=['Code'], properties={'value': 'ABC123'})
        db.create_node(labels=['Code'], properties={'value': 'XYZ456'})
        db.create_node(labels=['Code'], properties={'value': 'NODIGITS'})

        results = db.match_nodes(
            labels=['Code'],
            properties={'value': PropertyFilter.regex(r'\d+')}
        )

        assert len(results) == 2
        db.close()

    def test_regex_invalid_pattern_raises_error(self):
        """Test REGEX with invalid pattern raises error."""
        with pytest.raises(InvalidFilterError, match="Invalid regex pattern"):
            PropertyFilter.regex(r'[invalid(')

    def test_special_characters_in_contains(self):
        """Test CONTAINS with special LIKE characters (%, _)."""
        db = GrafitoDatabase()
        db.create_node(labels=['Data'], properties={'text': 'Value with 50% discount'})
        db.create_node(labels=['Data'], properties={'text': 'Normal text'})
        db.create_node(labels=['Data'], properties={'text': 'Another 50% off'})

        results = db.match_nodes(
            labels=['Data'],
            properties={'text': PropertyFilter.contains('50%')}
        )

        # Should find exactly those with "50%", not wildcard
        assert len(results) == 2
        db.close()

    def test_special_characters_in_starts_with(self):
        """Test STARTS_WITH with special characters."""
        db = GrafitoDatabase()
        db.create_node(labels=['File'], properties={'path': '[temp]file.txt'})
        db.create_node(labels=['File'], properties={'path': '[temp]doc.pdf'})
        db.create_node(labels=['File'], properties={'path': 'normal.txt'})

        results = db.match_nodes(
            labels=['File'],
            properties={'path': PropertyFilter.starts_with('[temp]')}
        )

        assert len(results) == 2
        db.close()

    def test_unicode_characters(self):
        """Test pattern matching with Unicode characters."""
        db = GrafitoDatabase()
        db.create_node(labels=['User'], properties={'name': 'José García'})
        db.create_node(labels=['User'], properties={'name': 'François Müller'})
        db.create_node(labels=['User'], properties={'name': 'John Smith'})

        results = db.match_nodes(
            labels=['User'],
            properties={'name': PropertyFilter.contains('García')}
        )

        assert len(results) == 1
        assert results[0].properties['name'] == 'José García'
        db.close()

    def test_empty_string_contains(self):
        """Test CONTAINS with empty string (should match all)."""
        db = GrafitoDatabase()
        db.create_node(labels=['Item'], properties={'name': 'Alice'})
        db.create_node(labels=['Item'], properties={'name': 'Bob'})
        db.create_node(labels=['Item'], properties={'name': ''})

        results = db.match_nodes(
            labels=['Item'],
            properties={'name': PropertyFilter.contains('')}
        )

        # Empty string is contained in all strings
        assert len(results) == 3
        db.close()

    def test_multiple_string_filters(self):
        """Test multiple string pattern filters in one query."""
        db = GrafitoDatabase()
        db.create_node(labels=['User'], properties={
            'name': 'Alice Johnson',
            'email': 'alice@example.com'
        })
        db.create_node(labels=['User'], properties={
            'name': 'Bob Smith',
            'email': 'bob@example.com'
        })
        db.create_node(labels=['User'], properties={
            'name': 'Alice Brown',
            'email': 'alice@gmail.com'
        })

        results = db.match_nodes(
            labels=['User'],
            properties={
                'name': PropertyFilter.starts_with('Alice'),
                'email': PropertyFilter.ends_with('@example.com')
            }
        )

        assert len(results) == 1
        assert results[0].properties['name'] == 'Alice Johnson'
        db.close()

    def test_string_matching_on_relationships(self):
        """Test string pattern matching on relationship properties."""
        db = GrafitoDatabase()
        alice = db.create_node(labels=['Person'], properties={'name': 'Alice'})
        company1 = db.create_node(labels=['Company'], properties={'name': 'TechCorp'})
        company2 = db.create_node(labels=['Company'], properties={'name': 'StartupInc'})
        company3 = db.create_node(labels=['Company'], properties={'name': 'TechStart'})

        db.create_relationship(alice.id, company1.id, 'WORKS_AT', {'role': 'Engineer'})
        db.create_relationship(alice.id, company2.id, 'APPLIED_TO', {'role': 'Manager'})
        db.create_relationship(alice.id, company3.id, 'WORKS_AT', {'role': 'Senior Engineer'})

        results = db.match_relationships(
            source_id=alice.id,
            properties={'role': PropertyFilter.contains('Engineer')}
        )

        assert len(results) == 2
        db.close()

    def test_contains_no_match(self):
        """Test CONTAINS with no matches."""
        db = GrafitoDatabase()
        db.create_node(labels=['User'], properties={'name': 'Alice'})
        db.create_node(labels=['User'], properties={'name': 'Bob'})

        results = db.match_nodes(
            labels=['User'],
            properties={'name': PropertyFilter.contains('Charlie')}
        )

        assert len(results) == 0
        db.close()

    def test_starts_with_no_match(self):
        """Test STARTS_WITH with no matches."""
        db = GrafitoDatabase()
        db.create_node(labels=['User'], properties={'name': 'Alice'})
        db.create_node(labels=['User'], properties={'name': 'Bob'})

        results = db.match_nodes(
            labels=['User'],
            properties={'name': PropertyFilter.starts_with('C')}
        )

        assert len(results) == 0
        db.close()

    def test_ends_with_no_match(self):
        """Test ENDS_WITH with no matches."""
        db = GrafitoDatabase()
        db.create_node(labels=['File'], properties={'name': 'doc.pdf'})
        db.create_node(labels=['File'], properties={'name': 'image.png'})

        results = db.match_nodes(
            labels=['File'],
            properties={'name': PropertyFilter.ends_with('.txt')}
        )

        assert len(results) == 0
        db.close()

    def test_regex_no_match(self):
        """Test REGEX with no matches."""
        db = GrafitoDatabase()
        db.create_node(labels=['User'], properties={'email': 'alice@example.com'})
        db.create_node(labels=['User'], properties={'email': 'bob@example.com'})

        results = db.match_nodes(
            labels=['User'],
            properties={'email': PropertyFilter.regex(r'.*@gmail\.com')}
        )

        assert len(results) == 0
        db.close()

    def test_case_sensitivity_matters(self):
        """Test that case sensitivity flag works correctly."""
        db = GrafitoDatabase()
        db.create_node(labels=['Item'], properties={'code': 'ABC123'})
        db.create_node(labels=['Item'], properties={'code': 'abc456'})
        db.create_node(labels=['Item'], properties={'code': 'XYZ789'})

        # Case-sensitive: should find only 'ABC123'
        results_sensitive = db.match_nodes(
            labels=['Item'],
            properties={'code': PropertyFilter.contains('ABC', case_sensitive=True)}
        )
        assert len(results_sensitive) == 1

        # Case-insensitive: should find both 'ABC123' and 'abc456'
        results_insensitive = db.match_nodes(
            labels=['Item'],
            properties={'code': PropertyFilter.contains('ABC', case_sensitive=False)}
        )
        assert len(results_insensitive) == 2
        db.close()

    def test_whitespace_in_patterns(self):
        """Test pattern matching with whitespace."""
        db = GrafitoDatabase()
        db.create_node(labels=['Text'], properties={'content': 'Hello World'})
        db.create_node(labels=['Text'], properties={'content': 'HelloWorld'})
        db.create_node(labels=['Text'], properties={'content': 'Hello  World'})  # Double space

        results = db.match_nodes(
            labels=['Text'],
            properties={'content': PropertyFilter.contains('Hello World')}
        )

        # Should match only exact "Hello World"
        assert len(results) == 1
        db.close()

    def test_regex_anchors(self):
        """Test REGEX with anchors (^ and $)."""
        db = GrafitoDatabase()
        db.create_node(labels=['Code'], properties={'value': '123'})
        db.create_node(labels=['Code'], properties={'value': '123456'})
        db.create_node(labels=['Code'], properties={'value': 'ABC123'})

        # Match exactly 3 digits
        results = db.match_nodes(
            labels=['Code'],
            properties={'value': PropertyFilter.regex(r'^\d{3}$')}
        )

        assert len(results) == 1
        assert results[0].properties['value'] == '123'
        db.close()

    def test_regex_case_insensitive_flag(self):
        """Test REGEX with case-insensitive matching using (?i) flag."""
        db = GrafitoDatabase()
        db.create_node(labels=['User'], properties={'name': 'Alice'})
        db.create_node(labels=['User'], properties={'name': 'ALICE'})
        db.create_node(labels=['User'], properties={'name': 'alice'})

        results = db.match_nodes(
            labels=['User'],
            properties={'name': PropertyFilter.regex(r'(?i)^alice$')}
        )

        assert len(results) == 3
        db.close()

    def test_backslash_in_string(self):
        """Test pattern matching with backslash characters."""
        db = GrafitoDatabase()
        db.create_node(labels=['Path'], properties={'value': r'C:\Users\Alice'})
        db.create_node(labels=['Path'], properties={'value': r'C:\Users\Bob'})
        db.create_node(labels=['Path'], properties={'value': r'/home/alice'})

        results = db.match_nodes(
            labels=['Path'],
            properties={'value': PropertyFilter.contains(r'C:\Users')}
        )

        assert len(results) == 2
        db.close()
