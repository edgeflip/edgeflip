# -*- coding: utf-8 -*-
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
