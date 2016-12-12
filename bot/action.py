""" Module for implementing new functionality in bot

"""
from abc import ABCMeta, abstractproperty

class Messaging(Exception):
    """ Error "used" to pass messages
    """
    pass

class BadInput(Exception):
    """ Error for bad input by user
    """
    def __init__(self, msg, args=tuple()):
        super(BadInput, self).__init__(msg)
        self.args = args

class Action(object):
    """ Abstract class for each functionality in bot

    Parameters
    ----------
    actor : Brain
        Bot that is performing the action
    """
    __metaclass__ = ABCMeta

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
