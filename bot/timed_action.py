""" Module for implementing functionality periodically within some time period

"""
import time
from .action import Action
from .brain import BadInput

class TimedAction(Action):
    """ Action class for repeating actions
    """
    def __init__(self, actor):
        """ Initializer of action

        Parameters
        ----------
        actor : Brain
            Brain instance that describes the acting bot
        """
        self.actor = actor

    @property
    def name(self):
        return 'timing actions'

    @property
    def init_response(self):
        return ('I can only do one of {0}'
                ' when managing timed actions').format(self.options.keys())

    @property
    def options(self):
        return {'recount' : self.recount,
                'add' : self.add,
                'remove' : self.remove}

    def recount(self):
        """ Shows all periodic functions/actions

        """
        msg = 'Here are the registered timed actions:\n'
        for (action, option, inputs, interval), last_time in self.actor.timed_actions.iteritems():
            msg += ('Command: {0} {1} {2}\n'
                    'Time Interval: {3}\n'
                    'Last Time: {4}\n'.format(action.name, option, inputs, interval, last_time))
        # I'm being lazy here. Because I need the channel to speak, but I think
        # channel should be independent of the action
        raise BadInput(msg)

    def add(self, interval='', action='', *commands):
        """ Adds a new periodic function

        Parameters
        ----------
        interval : str
            Interval by which the function/action will be run
            Can be turned into a number
        action : str
            Name of the action that will be run
        commands : list
            List of string of commands that are necessary to run the command
            Needs option (which function within action)
            Needs input for the function within action
        """
        error_msg = ''
        if interval == '' or action == '' or len(commands) == 0:
            error_msg += 'I will help you add timed actions.\n'
        try:
            interval = int(interval)
        except (ValueError, IndexError):
            error_msg += ('First option specifies how often the action is repeated.'
                          ' It must be a number.\n')

        allowed_actions = [i for i in self.actor.actions if i != self.name]
        if action not in allowed_actions:
            error_msg += ('Second option onwards specify what is done.'
                          ' It must be one of {0}.\n'.format(allowed_actions))
        if error_msg != '':
            raise BadInput(error_msg)

        action = self.actor.actions[action]
        option = commands[0]
        inputs = commands[1:]
        action.options[option](*inputs)
        self.actor.timed_actions[(action, option, inputs, interval)] = time.time()

    def remove(self, action='', *commands):
        """ Removes a periodic function from list

        Parameters
        ----------
        action : str
            Name of the action
        commands : list
            List of string of commands that are necessary to run the command
            Needs option (which function within action)
            Needs input for the function within action
        """
        error_msg = ''
        if len(commands) == 0 or commands[0] == '':
            error_msg += 'I will help you manage timed actions.\n'
            error_msg += ('Repeat the command that you would like to remove.'
                          ' See `@ayerslab_bot timing actions recount` for a list of commands')
        if error_msg != '':
            raise BadInput(error_msg)

    #TODO: modify
