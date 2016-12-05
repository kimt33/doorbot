from abc import ABCMeta, abstractproperty, abstractmethod

class BadInputError(Exception):
    pass

class Action(object):
    __metaclass__ = ABCMeta

    # response
    # action
    #
    def __init__(self, actor):
        self.actor = actor

    @abstractproperty
    def name(self):
        return 'name of action'

    @abstractproperty
    def init_response(self):
        return 'response to inadequate option'

    @abstractproperty
    def options(self):
        return {'options for action' : 'function for option'}
