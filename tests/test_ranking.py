#!/usr/bin/env python

import json
import unittest
import datetime

from edgeflip import datastructs
from edgeflip import ranking


def loadEdgesFromFile(edgesFile):

    StrToDate = lambda s: datetime.datetime.strptime(s, "%Y-%m-%d").date() if s else None

    userDict = json.load(open(edgesFile, 'r'))
    primDict = userDict['primary_info']
    primInfo = datastructs.UserInfo(
        uid=primDict['fbid'],
        first_name=primDict['first_name'],
        last_name=primDict['last_name'],
        sex=primDict['gender'],
        birthday=StrToDate(primDict.get('birthday')),
        city=primDict['city'],
        state=primDict['state']
        )

    edges = []
    for friendDict in userDict['friends']:
        secDict = friendDict['secondary_info']
        edgeDict = friendDict['edge']

        secInfo = datastructs.FriendInfo(
            primId=primDict['fbid'],
            friendId=secDict['fbid'],
            first_name=secDict['first_name'],
            last_name=secDict['last_name'],
            sex=secDict.get('gender'),
            birthday=StrToDate(secDict.get('birthday')),
            city=secDict.get('city'),
            state=secDict.get('state'),
            primPhotoTags=edgeDict.get('photoPrim'),
            otherPhotoTags=edgeDict.get('photoOth'),
            mutual_friend_count=edgeDict.get('muts')
            )

        ecIn = datastructs.EdgeCounts(
            secInfo.id, 
            primInfo.id,
            postLikes=edgeDict.get('postLikesIn'), 
            postComms=edgeDict.get('postCommsIn'), 
            statLikes=edgeDict.get('statLikesIn'), 
            statComms=edgeDict.get('statCommsIn'), 
            wallPosts=edgeDict.get('wallPostsIn'), 
            wallComms=edgeDict.get('wallCommsIn'),
            tags=edgeDict.get('tagsIn'), 
            photoTarg=secInfo.primPhotoTags, 
            photoOth=secInfo.otherPhotoTags, 
            muts=secInfo.mutuals
            )

        ecOut = datastructs.EdgeCounts(
            primInfo.id, 
            secInfo.id,
            postLikes=edgeDict.get('postLikesOut'), 
            postComms=edgeDict.get('postCommsOut'), 
            statLikes=edgeDict.get('statLikesOut'), 
            statComms=edgeDict.get('statCommsOut'), 
            wallPosts=edgeDict.get('wallPostsOut'), 
            wallComms=edgeDict.get('wallCommsOut'),
            tags=edgeDict.get('tagsOut'), 
            photoTarg=None, 
            photoOth=None, 
            muts=None
            )

        edge = datastructs.Edge(primInfo, secInfo, ecIn, ecOut)

        edges.append(edge)

    return edges



edges = loadEdgesFromFile('testEdges.json')

class TestRanking(unittest.TestCase):
#    def test_something(self):
#        self.assertEqual(val, func(args)) or self.assertRaises(ErrorType, lambda: func(args))

    """All of the values here refer to the test edges in testEdges.json"""

    def test_edge_aggregator_inPhotoTarget(self):
        self.assertEqual(1, ranking.EdgeAggregator(edges, max, True, True).inPhotoTarget)

    def test_edge_aggregator_inPhotoOther(self):
        self.assertEqual(0, ranking.EdgeAggregator(edges, max, True, True).inPhotoOther)

    def test_edge_aggregator_mutuals(self):
        self.assertEqual(3, ranking.EdgeAggregator(edges, max, True, True).inMutuals)

    def test_edge_aggregator_inPostLikes(self):
        self.assertEqual(1, ranking.EdgeAggregator(edges, max, True, True).inPostLikes)

    def test_edge_aggregator_inPostComms(self):
        self.assertEqual(1, ranking.EdgeAggregator(edges, max, True, True).inPostComms)

    def test_edge_aggregator_inStatLikes(self):
        self.assertEqual(2, ranking.EdgeAggregator(edges, max, True, True).inStatLikes)

    def test_edge_aggregator_inStatComms(self):
        self.assertEqual(1, ranking.EdgeAggregator(edges, max, True, True).inStatComms)

    def test_edge_aggregator_inWallPosts(self):
        self.assertEqual(3, ranking.EdgeAggregator(edges, max, True, True).inWallPosts)

    def test_edge_aggregator_inWallComms(self):
        self.assertEqual(1, ranking.EdgeAggregator(edges, max, True, True).inWallComms)

    def test_edge_aggregator_inTags(self):
        self.assertEqual(4, ranking.EdgeAggregator(edges, max, True, True).inTags)


    def test_edge_aggregator_outPostLikes(self):
        self.assertEqual(6, ranking.EdgeAggregator(edges, max, True, True).outPostLikes)

    def test_edge_aggregator_outPostComms(self):
        self.assertEqual(2, ranking.EdgeAggregator(edges, max, True, True).outPostComms)

    def test_edge_aggregator_outStatLikes(self):
        self.assertEqual(3, ranking.EdgeAggregator(edges, max, True, True).outStatLikes)

    def test_edge_aggregator_outStatComms(self):
        self.assertEqual(1, ranking.EdgeAggregator(edges, max, True, True).outStatComms)

    def test_edge_aggregator_outWallPosts(self):
        self.assertEqual(0, ranking.EdgeAggregator(edges, max, True, True).outWallPosts)

    def test_edge_aggregator_outWallComms(self):
        self.assertEqual(4, ranking.EdgeAggregator(edges, max, True, True).outWallComms)

    def test_edge_aggregator_outTags(self):
        self.assertEqual(3, ranking.EdgeAggregator(edges, max, True, True).outTags)


    def test_prox(self):
        self.assertEqual(0.671, round(ranking.prox(edges[0], ranking.EdgeAggregator(edges, max, True, True)), 3))


    def test_getFriendRanking(self):
        self.assertEqual([2,4,3], [e.secondary.id for e in ranking.getFriendRanking(edges, True, True)])


if __name__ == '__main__':
    unittest.main()
