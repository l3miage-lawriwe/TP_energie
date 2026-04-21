'''
Mother class for heuristics.

@author: Vassilissa Lehoux
'''
from typing import Dict, Optional

from src.scheduling.instance.instance import Instance
from src.scheduling.solution import Solution


class Heuristic(object):
    '''
    classdocs
    '''

    def __init__(self, params: Optional[Dict] = None):
        '''
        Constructor
        @param params: The parameters of your heuristic method if any as a
               dictionary. Implementation should provide default values in the function.
        '''
        self.params = dict(params or {})

    def run(self, instance: Instance, params: Optional[Dict] = None) -> Solution:
        '''
        Computes a solution for the given instance.
        Implementation should provide default values in the function
        (the function will be evaluated with an empty dictionary).
        @param instance: the instance to solve
        @param params: the parameters for the run
        '''
        raise NotImplementedError("Heuristic.run must be implemented in subclasses")

