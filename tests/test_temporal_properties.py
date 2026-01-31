"""Tests for temporal property storage, filtering, and ordering."""

from datetime import date, datetime, time, timedelta, timezone

from grafito import GrafitoDatabase, PropertyFilter


class TestTemporalProperties:
    """Validate temporal property handling with dates, times, and timezones."""

    def test_temporal_properties_are_normalized(self):
        """Store temporal properties and confirm ISO normalization."""
        db = GrafitoDatabase(':memory:')
        tz_plus2 = timezone(timedelta(hours=2))

        node = db.create_node(
            labels=['Event'],
            properties={
                'd': date(2024, 1, 2),
                'dt_naive': datetime(2024, 1, 2, 10, 11, 12),
                'dt_utc': datetime(2024, 1, 2, 10, 11, 12, tzinfo=timezone.utc),
                'dt_offset': datetime(2024, 1, 2, 10, 11, 12, tzinfo=tz_plus2),
                't_naive': time(10, 11, 12),
                't_offset': time(10, 11, 12, tzinfo=tz_plus2),
            },
        )

        stored = db.get_node(node.id).properties
        assert stored['d'] == '2024-01-02'
        assert stored['dt_naive'] == '2024-01-02T10:11:12'
        assert stored['dt_utc'] == '2024-01-02T10:11:12Z'
        assert stored['dt_offset'] == '2024-01-02T10:11:12+02:00'
        assert stored['t_naive'] == '10:11:12'
        assert stored['t_offset'] == '10:11:12+02:00'
        db.close()

    def test_date_filters_support_comparisons(self):
        """Date filters should support gt/lt/between semantics."""
        db = GrafitoDatabase(':memory:')
        db.create_node(labels=['Event'], properties={'d': date(2024, 1, 1)})
        db.create_node(labels=['Event'], properties={'d': date(2024, 1, 2)})
        db.create_node(labels=['Event'], properties={'d': date(2024, 1, 10)})

        results = db.match_nodes(
            labels=['Event'],
            properties={'d': PropertyFilter.gt(date(2024, 1, 2))}
        )
        assert [n.properties['d'] for n in results] == ['2024-01-10']

        results = db.match_nodes(
            labels=['Event'],
            properties={'d': PropertyFilter.lt(date(2024, 1, 2))}
        )
        assert [n.properties['d'] for n in results] == ['2024-01-01']

        results = db.match_nodes(
            labels=['Event'],
            properties={'d': PropertyFilter.between(date(2024, 1, 1), date(2024, 1, 2))}
        )
        assert sorted(n.properties['d'] for n in results) == ['2024-01-01', '2024-01-02']
        db.close()

    def test_datetime_filters_support_utc_comparisons(self):
        """Datetime filters should support comparisons with UTC values."""
        db = GrafitoDatabase(':memory:')
        db.create_node(
            labels=['Event'],
            properties={'dt': datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)},
        )
        db.create_node(
            labels=['Event'],
            properties={'dt': datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)},
        )
        db.create_node(
            labels=['Event'],
            properties={'dt': datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc)},
        )

        results = db.match_nodes(
            labels=['Event'],
            properties={'dt': PropertyFilter.gte(datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc))}
        )
        assert sorted(n.properties['dt'] for n in results) == [
            '2024-01-02T10:00:00Z',
            '2024-01-03T10:00:00Z',
        ]

        results = db.match_nodes(
            labels=['Event'],
            properties={'dt': PropertyFilter.between(
                datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
            )}
        )
        assert sorted(n.properties['dt'] for n in results) == [
            '2024-01-01T10:00:00Z',
            '2024-01-02T10:00:00Z',
        ]
        db.close()

    def test_time_filters_support_comparisons(self):
        """Time filters should support comparisons for naive values."""
        db = GrafitoDatabase(':memory:')
        db.create_node(labels=['Event'], properties={'t': time(9, 0, 0)})
        db.create_node(labels=['Event'], properties={'t': time(10, 0, 0)})
        db.create_node(labels=['Event'], properties={'t': time(11, 0, 0)})

        results = db.match_nodes(
            labels=['Event'],
            properties={'t': PropertyFilter.gt(time(9, 30, 0))}
        )
        assert sorted(n.properties['t'] for n in results) == ['10:00:00', '11:00:00']

        results = db.match_nodes(
            labels=['Event'],
            properties={'t': PropertyFilter.between(time(9, 0, 0), time(10, 0, 0))}
        )
        assert sorted(n.properties['t'] for n in results) == ['09:00:00', '10:00:00']
        db.close()

    def test_datetime_offset_values_match_same_offset(self):
        """Datetime filters should match stored offsets when values use same offset."""
        db = GrafitoDatabase(':memory:')
        tz_plus2 = timezone(timedelta(hours=2))

        node = db.create_node(
            labels=['Event'],
            properties={'dt': datetime(2024, 1, 2, 10, 0, 0, tzinfo=tz_plus2)},
        )

        results = db.match_nodes(
            labels=['Event'],
            properties={'dt': datetime(2024, 1, 2, 10, 0, 0, tzinfo=tz_plus2)}
        )
        assert [n.id for n in results] == [node.id]
        db.close()

    def test_temporal_ordering_by_date(self):
        """Ordering by date should follow ISO chronological order."""
        db = GrafitoDatabase(':memory:')
        db.create_node(labels=['Event'], properties={'d': date(2024, 1, 3)})
        db.create_node(labels=['Event'], properties={'d': date(2024, 1, 1)})
        db.create_node(labels=['Event'], properties={'d': date(2024, 1, 2)})

        results = db.match_nodes(labels=['Event'], order_by='d', ascending=True)
        assert [n.properties['d'] for n in results] == [
            '2024-01-01',
            '2024-01-02',
            '2024-01-03',
        ]

        results = db.match_nodes(labels=['Event'], order_by='d', ascending=False)
        assert [n.properties['d'] for n in results] == [
            '2024-01-03',
            '2024-01-02',
            '2024-01-01',
        ]
        db.close()

    def test_temporal_ordering_by_datetime_utc(self):
        """Ordering by datetime should follow UTC ISO order."""
        db = GrafitoDatabase(':memory:')
        db.create_node(
            labels=['Event'],
            properties={'dt': datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)},
        )
        db.create_node(
            labels=['Event'],
            properties={'dt': datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)},
        )
        db.create_node(
            labels=['Event'],
            properties={'dt': datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc)},
        )

        results = db.match_nodes(labels=['Event'], order_by='dt', ascending=True)
        assert [n.properties['dt'] for n in results] == [
            '2024-01-01T10:00:00Z',
            '2024-01-02T10:00:00Z',
            '2024-01-03T10:00:00Z',
        ]
        db.close()

    def test_temporal_ordering_by_time(self):
        """Ordering by time should follow ISO time order."""
        db = GrafitoDatabase(':memory:')
        db.create_node(labels=['Event'], properties={'t': time(10, 0, 0)})
        db.create_node(labels=['Event'], properties={'t': time(9, 0, 0)})
        db.create_node(labels=['Event'], properties={'t': time(11, 0, 0)})

        results = db.match_nodes(labels=['Event'], order_by='t', ascending=True)
        assert [n.properties['t'] for n in results] == ['09:00:00', '10:00:00', '11:00:00']
        db.close()
