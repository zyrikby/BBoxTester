'''
Created on Sep 30, 2014

@author: yury
'''

class MsgException(Exception):
    '''
    Generic exception with an optional string msg.
    '''
    def __init__(self, msg=""):
        self.msg = msg
    