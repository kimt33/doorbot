""" Module for implementing new functionality in bot

"""
from abc import ABCMeta, abstractproperty

class BadInputError(Exception):
    """ Error for bad input by user
    """
    def __init__(self, msg, args=tuple()):
        self.msg = msg
        self.args = args

class Action(object):
    """ Abstract class for each functionality in bot

    Parameters
    ----------
    actor : Brain
        Bot that is performing the action
    """
    __metaclass__ = ABCMeta

    def __init__(self, actor):
        """ Initializer of action
        """
        self.actor = actor

    @abstractproperty
    def name(self):
        """ Name of action/functionality as seen by the user
        """
        return 'name of action'

    @abstractproperty
    def init_response(self):
        """ Response to bad selection by user
        """
        return 'response to inadequate option'

    @abstractproperty
    def options(self):
        """ List/Dictionary of options available to the user within a functionality
        """
        return {'options for action' : 'function for option'}
