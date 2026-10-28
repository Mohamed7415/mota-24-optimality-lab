"""Copy a numerical OriginalRoute while dropping noncausal diagnostic history.
Only events/timeline/draw history is discarded, not root, RNG state or recorded
route actions. OriginalRoute.battle slices only newly appended draws.
"""
import copy

def clone_for_search(route):
    memo={id(getattr(route,name)):[] for name in ('events','timeline','draws')}
    return copy.deepcopy(route,memo)
