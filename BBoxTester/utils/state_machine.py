'''
Created on Oct 14, 2014

@author: Yury Zhauniarovich <y.zhalnerovich{at}gmail.com>
'''
from bbox_core.bboxreporter import MsgException

class StateMachine:
    '''
    A simple state machine class.
    '''
    def __init__(self, states = []):
        '''
        Constructor.
        
        Args:
            :param states: list of possible states and allowed transitions
        '''
        '''
        Constructor
        '''
        self._states = states
        self.currentState = None
        
    def start(self, startState):
        '''
        Start the state machine from a predifined state
        
        Args:
            :param startState: state from which to start machine.
        '''
        if not startState or (startState not in [x[0] for x in self._states]):
            raise ValueError("Not a valid start state")
        self.currentState = startState
        
    def stop(self):
        '''
        Stops the state machine
        '''
        self.currentState = None
    
    
    def isTransitionPossible(self, toState):
        if not self.currentState:
            raise TransitionNotPossible("StateMachine not Started - cannot process request!")
        
        if not toState:
            return False
        
        # get a list of transitions which are valid       
        nextStates = [x[1] for x in self._states if x[0] == self.currentState]
        if not nextStates or (toState not in nextStates):
            return False
        return True
    
#     def isTransitionFromCurrentPossible(self, toState):
#         if not self.currentState:
#             raise TransitionNotPossible("StateMachine not Started - cannot process request!")
#         
#         if not toState:
#             raise ValueError("Not a valid start state")
#         
#         prevStates = [x[0] for x in self._states if x[1] == toState]
#         if not prevStates or (self.currentState not in prevStates):
#             return False
#         return True
    
    def transitToState(self, toState):
        if not self.currentState:
            raise TransitionNotPossible("StateMachine not Started - cannot process request!")
        
        if not toState:
            raise TransitionNotPossible("Cannot switch to undefined state!")
        
        # get a list of transitions which are valid       
        nextStates = [x[1] for x in self._states if x[0] == self.currentState]
        if not nextStates or (toState not in nextStates):
            raise TransitionNotPossible("Transition from [%s] to [%s] is not allowed!" % (str(self.currentState), str(toState)))
        
        if (toState == self.currentState):
            return False
        
        self.currentState = toState
        return True
    
    def getCurrentState(self):
        return self.currentState
    


class TransitionNotPossible(MsgException):
    '''
    State transition is not possible!
    '''
    