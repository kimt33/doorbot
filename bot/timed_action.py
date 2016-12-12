""" Module for implementing functionality periodically within some time period

"""
import time
from .action import Action, BadInput, Messaging
from .utils import nice_options

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
        return ('I can only do one of {0} when managing timed actions.'
                ''.format(nice_options(self.options.keys(), 'or')))

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
                    'Last Time: {4}\n\n'.format(action.name, option, inputs, interval, last_time))
        # I'm being lazy here. Because I need the channel to speak, but I think
        # channel should be independent of the action
        raise Messaging(msg)

    def add(self, interval='', action='', option='', *commands):
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
        try:
            interval = int(interval)
        except (ValueError, IndexError):
            raise BadInput('How often should the action be repeated?')

        allowed_actions = [i for i in self.actor.actions if i != self.name]
        if action not in allowed_actions:
            raise BadInput('What command would you like me to repeat?'
                           ' It should be one of {0}.'
                           ''.format(nice_options(allowed_actions)),
                           args=(str(interval),))

        action = self.actor.actions[action]
        if option not in action.options:
            raise BadInput(action.init_response, args=(str(interval), action.name))
        # ugh
        inputs = tuple(commands)
        try:
            action.options[option](*inputs)
            self.actor.timed_actions[(action.name, option, inputs, interval)] = time.time()
        except BadInput as handler:
            raise BadInput(handler.message, args=(str(interval), action.name, option) + handler.args)
        except Messaging as handler:
            self.actor.timed_actions[(action, option, inputs, interval)] = time.time()
            raise handler

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
