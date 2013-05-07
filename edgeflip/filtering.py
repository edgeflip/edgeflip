"""functions for filtering


TODO: These can go away, but we'll probably want to move the filter-specific
      stuff from client_db_tools.py in here (which is where all this logic
      has moved at this point) -- Kit
"""

import logging
logger = logging.getLogger(__name__)

def getBestSecStateFromEdges(edgesRanked, statePool=None, eligibleProportion=0.5):
    """move to filtering module"""
    edgesSort = sorted(edgesRanked, key=lambda x: x.score, reverse=True)
    elgCount = int(len(edgesRanked) * eligibleProportion)
    edgesElg = edgesSort[:elgCount]  # only grab the top x% of the pool
    state_count = {}
    for e in edgesElg:
        state_count[e.secondary.state] = state_count.get(e.secondary.state, 0) + 1
    if (statePool is not None):
        for state in state_count.keys():
            if (state not in statePool):
                del state_count[state]
    if (state_count):
        logger.debug("best state counts: %s", str(state_count))
        bestCount = max(state_count.values() + [0])  # in case we don't get any states
        bestStates = [ state for state, count in state_count.items() if (count == bestCount) ]
        if (len(bestStates) == 1):
            logger.debug("best state returning %s", bestStates[0])
            return bestStates[0]
        else:
            # there's a tie for first, so grab the state with the best avg scores
            bestState = None
            bestScoreAvg = 0.0
            for state in bestStates:
                edgesState = [ e for e in edgesElg if (e.state == state) ]
                scoreAvg = sum([ e.score for e in edgesState ])
                if (scoreAvg > bestScoreAvg):
                    bestState = state
                    bestScoreAvg = scoreAvg
            logger.debug("best state returning %s", bestState)
            return bestState
    else:
        return None

def filterEdgesBySec(edges, filterTups):  # filterTups are (attrName, compTag, attrVal)
    """move to filtering module"""
    str_func = { "min": lambda x, y: x > y, "max": lambda x, y: x < y, "eq": lambda x, y: x == y }
    edgesGood = edges[:]
    for attrName, compTag, attrVal in filterTups:
        logger.debug("filtering %d edges on '%s %s %s'", len(edgesGood), attrName, compTag, attrVal)
        filtFunc = lambda e: hasattr(e.secondary, attrName) and str_func[compTag](e.secondary.__dict__[attrName], attrVal)
        edgesGood = [ e for e in edgesGood if filtFunc(e) ]
        logger.debug("have %d edges left", len(edgesGood))
    return edgesGood
