""" Module for implementing new actions that are initiated by the bot

e.g. Asking users for something

"""
import time
from .action import Action, BadInput
from .utils import nice_options

class InteractiveAction(Action):
    """ Action class for actions that are started by the bot
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
        return 'interactive actions'

    @property
    def init_response(self):
        return ('I can only do one of {0} when managing timed actions.'
                ''.format(nice_options(self.options.keys(), 'or')))

    @property
    def options(self):
        return {
                'ask' : self.ask,
                }

    def is_valid_channel(self, channel):
        """ Checks if channel is valid

        Parameters
        ----------
        channel : str
            Name of channel

        Returns
        -------
        True if channel is valid
        False if channel is not valid
        """
        return channel in (self.actor.public_channels.keys() +
                           self.actor.private_channels.keys() +
                           self.actor.dm_channels.keys())

    def ask(self, channels='', ice_breaker='', kwrds_response='', action='', option='', inputs=''):
        """ Asks users for input (after telling it what to ask) and executes
        the provided function

        Parameters
        ----------
        channels : str
            Channels to ask
            Must be given as a string of tuple '(one, two, three)'.
        ice_breaker : str
            First thing that the bot says
        kwrd_response : str
            List of alternating keywords and responses to keywords
        action : str
            Name of the action that will be run
        option : str
            Specific method of the action that will be run
        commands : list
            List of string of commands that are necessary to run the command
            Needs option (which function within action)
            Needs input for the function within action

        Note
        ----
        Because Brain.process passes input by a single list of strings, it's kind
        of difficult to pass these arguments into a function if there are more than
        one lists that are variable.
        For example, if I have two variable lists as inputs, then I must know where
        to separate a single list of inputs into two pieces, i.e. how many elements
        are in each list. Otherwise, the two lists can get mixed up.
        """
        # FIXME: eval

        if channels == 'everyone':
            channels = tuple(self.actor.public_channels.keys())
        elif channels == '':
            raise BadInput('Provide the channels you would like to ask.'
                           "Channels must be given in the form `('channel_one', 'channel_two',)`"
                           " i.e. python syntax for tuple")
        else:
            try:
                channels = eval(channels)
            except (NameError,SyntaxError):
                raise BadInput("Channels must be given in the form `('channel_one', 'channel_two',)`"
                               " i.e. python syntax for tuple")

            for channel in channels:
                if not self.is_valid_channel(channel):
                    raise BadInput('I can\'t find the channel called {0}.'.format(channel))

        if ice_breaker == '':
            raise BadInput('What would you like me to say to everyone?',
                            args=(str(channels), ))

        if kwrds_response == '':
            raise BadInput('Could you give me keywords and my response to these keywords?'
                           " They should be of the form `{('keyword1','keyword2'):'response1',}`"
                           ' i.e. python syntax for dictionary',
                            args=(str(channels), ice_breaker))
        else:
            try:
                kwrds_response = eval(kwrds_response)
            except (NameError,SyntaxError):
                raise BadInput("Keywords and responses should be in the form"
                               " `{('keyword1','keyword2'):'response1',}`"
                               ' i.e. python syntax for dictionary',
                               args=(str(channels), ice_breaker))

        allowed_actions = [i for i in self.actor.actions if i not in (self.name, 'timing actions')]
        if action not in allowed_actions:
            raise BadInput('What command would you like me?'
                           ' It should be one of {0}.'
                           ''.format(nice_options(allowed_actions)),
                           args=(str(channels), ice_breaker, str(kwrds_response)))

        action = self.actor.actions[action]
        if option not in action.options:
            raise BadInput(action.init_response,
                           args=(str(channels), ice_breaker, str(kwrds_response),
                                 action.name))

        if inputs == '':
            raise BadInput('The following inputs are needed to run the'
                           ' command with appropriate options.'
                           ' Because I am a fucking idiot, I cannot check'
                           ' if your inputs are valid until someone replies.'
                           ' So make sure they are correct.\n'
                           'If you want the function to involve the user'
                           ' that replies, write `user`.\n'
                           "The inputs must be given in the form `('input1', 'input2')`"
                           ' i.e. python syntax for tuple of strings.',
                           args=(str(channels), ice_breaker, str(kwrds_response),
                                 action.name, option))
        else:
            try:
                kwrds_response = eval(inputs)
            except (NameError, SyntaxError):
                raise BadInput("The inputs must be given in the form `('input1', 'input2')`"
                               ' i.e. python syntax for tuple of strings.',
                               args=(str(channels), ice_breaker, str(kwrds_response),
                                     action.name, option))

        for channel in channels:
            self.actor.speak(channel, ice_breaker)
            # NOTE: kills all conversations that were already happening in these channels
            if channel in self.actor.commmands:
                self.actor.conversations[channel] = ('', time.time(), 'conversation',
                                                     'converse')
        # process user response
        self.actor.process()

        print channels, ice_breaker, kwrds_response, action, option, inputs
