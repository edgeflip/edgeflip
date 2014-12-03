# -*- coding: utf-8 -*-
import datetime

from django.db import models
from django.test import TestCase

from core.db.models import sql


class QuerySerializationTestCase(TestCase):

    @classmethod
    def setupClass(cls):
        class Parent(models.Model):

            parent_field = models.CharField()

        class Child(models.Model):

            child_field = models.CharField()
            parent = models.ForeignKey(Parent)

            class Meta(object):
                db_table = 'children'

        cls.Parent = Parent
        cls.Child = Child


class TestEquivalentSerialization(QuerySerializationTestCase):

    def setUp(self):
        self.parent = self.Parent(id=1)
        self.query_sets = (
            self.Child.objects.filter(parent_id=1, child_field='this-one'),
            self.Child.objects.filter(parent_id=1L, child_field=u'this-one'),
            self.Child.objects.filter(parent=self.parent, child_field='this-one'),
            self.parent.child_set.filter(child_field='this-one'),
        )

    def test_serialization(self):
        expected = (
            # Tables
            frozenset([u'children']),
            # Conditions
            (
                False,
                u'AND',
                frozenset([(u'children', u'child_field', u'exact', True, u'this-one'),
                           (u'children', u'parent_id', u'exact', True, 1L)]),
            ),
        )
        for query_set in self.query_sets:
            actual = sql.serialize_query(query_set.query)
            self.assertEqual(actual, expected)

    def test_hash(self):
        expected = 'c3bf8c32a800d765c22d94bbc945a443'
        for query_set in self.query_sets:
            actual = sql.hash_query(query_set.query)
            self.assertEqual(actual, expected)


class TestUtf8Serialization(QuerySerializationTestCase):

    def test_serialization(self):
        query_set = self.Child.objects.filter(parent_id=1L, child_field=u'thís-øne')
        actual = sql.serialize_query(query_set.query)
        self.assertEqual(actual, (
            # Tables
            frozenset([u'children']),
            # Conditions
            (
                False,
                u'AND',
                frozenset([(u'children', u'child_field', u'exact', True, u'thís-øne'),
                           (u'children', u'parent_id', u'exact', True, 1L)]),
            ),
        ))

    def test_hash(self):
        query_set = self.Child.objects.filter(parent_id=1L, child_field=u'thís-øne')
        actual = sql.hash_query(query_set.query)
        self.assertEqual(actual, '761c013158cf0be095b7ea575828269e')


class TestSerialization(QuerySerializationTestCase):

    @classmethod
    def setupClass(cls):
        super(TestSerialization, cls).setupClass()

        class BetterChild(models.Model):

            child_field = models.CharField()
            parent = models.ForeignKey(cls.Parent)
            created = models.DateTimeField(auto_now_add=True)

            class Meta(object):
                db_table = 'children'

        cls.BetterChild = BetterChild

    def test_all(self):
        query_set = self.Child.objects.all()
        actual = sql.serialize_query(query_set.query)
        self.assertEqual(actual, (
            frozenset([u'children']),
            (),
        ))

    def test_filter(self):
        query_set = self.Child.objects.filter(parent_id=1, child_field='this-one')
        actual = sql.serialize_query(query_set.query)
        self.assertEqual(actual, (
            # Tables
            frozenset([u'children']),
            # Conditions
            (
                False,
                u'AND',
                frozenset([(u'children', u'child_field', u'exact', True, u'this-one'),
                           (u'children', u'parent_id', u'exact', True, 1L)]),
            ),
        ))

    def test_exclude(self):
        query_set = self.Child.objects.exclude(parent_id=1, child_field='this-one')
        actual = sql.serialize_query(query_set.query)
        self.assertEqual(actual, (
            frozenset([u'children']),
            (
                # Always starts with non-exclusionary base
                False,
                u'AND',
                frozenset([
                    # Condition is itself a "where" node (i.e. parenthetical)
                    (
                        True, # NOT ...
                        u'AND',
                        frozenset([(u'children', u'child_field', u'exact', True, u'this-one'),
                                   (u'children', u'parent_id', u'exact', True, 1L)]),
                    ),
                ]),
            ),
        ))

    def test_exclude_multi(self):
        query_set = self.Child.objects.exclude(parent_id=1).exclude(child_field='this-one')
        actual = sql.serialize_query(query_set.query)
        self.assertEqual(actual, (
            frozenset([u'children']),
            (
                False,
                u'AND',
                frozenset([
                    (
                        True, # NOT ...
                        u'AND',
                        frozenset([(u'children', u'child_field', u'exact', True, u'this-one')]),
                    ),
                    (
                        True, # NOT ...
                        u'AND',
                        frozenset([(u'children', u'parent_id', u'exact', True, 1L)]),
                    ),
                ]),
            ),
        ))

    def test_or(self):
        query_set = self.Child.objects.filter(
            models.Q(parent_id=1) | models.Q(child_field='this-one')
        )
        actual = sql.serialize_query(query_set.query)
        self.assertEqual(actual, (
            # Tables
            frozenset([u'children']),
            # Conditions
            (
                # Always starts with non-exclusionary base
                False,
                u'AND',
                frozenset([
                    # Condition is itself a "where" node (i.e. parenthetical)
                    (
                        False,
                        u'OR',
                        frozenset([(u'children', u'child_field', u'exact', True, u'this-one'),
                                   (u'children', u'parent_id', u'exact', True, 1L)]),
                    ),
                ]),
            ),
        ))

    def test_filter_in(self):
        query_set = self.Child.objects.filter(child_field__in=['this-one', 'that-one'])
        actual = sql.serialize_query(query_set.query)
        self.assertEqual(actual, (
            frozenset(['children']),
            (
                False,
                'AND',
                frozenset([(u'children', u'child_field', u'in', True, frozenset(['this-one', 'that-one']))]),
            ),
        ))

    def test_filter_range(self):
        query_set = self.BetterChild.objects.filter(created__range=[
            datetime.date(2010, 1, 10),
            datetime.datetime(2011, 5, 15, 8, 10, 10)
        ])
        actual = sql.serialize_query(query_set.query)
        self.assertEqual(actual, (
            frozenset(['children']),
            (
                False,
                'AND',
                frozenset([(u'children', u'created', u'range', datetime.datetime, (
                    '2010-01-10 00:00:00-06:00', # applies CST
                    '2011-05-15 08:10:10-05:00' # applies CDT
                ))]),
            ),
        ))
