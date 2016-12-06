from . import ear
from . import mouth
from .action import BadInputError
from .timed_action import TimedAction

class Brain(object):
    def __init__(self, bot_id, slack_client):
        self.bot_id = bot_id
        self.slack_client = slack_client
        self.actions = {i.name:i for i in [
                                           TimedAction(self)]}
        # dictionary of (action, options, inputs, interval) : last time acted
        self.timed_actions = {}

    @property
    def call_name(self):
        return "<@{0}>".format(self.bot_id)

    def listen(self, slack_rtm_output):
        """
            The Slack Real Time Messaging API is an events firehose.
            this parsing function returns None unless a message is
            directed at the Bot, based on its ID.
        """
        return ear.listen(self, slack_rtm_output)

    def speak(self, channel, response):
        return mouth.speak(self, channel, response)

    def process(self, command, channel):
        """ Processes the command

        Parameters
        ----------
        command : str
            Direct message that contains the command
        channel : str
            Channel from which the message arrived

        Returns
        -------
        """
        sel_actions = [(action, name) for action, name in self.actions.iteritems() if name in command]
        if len(sel_actions) > 1:
            self.speak(channel, 'I can only handle one command.')
        elif len(sel_actions) == 0:
            self.speak(channel, 'I can only do one of {0}.'.format(self.actions))
        action, action_name = sel_actions[0]
        option_and_inputs = command.split(action_name)[1].split()
        if len(option_and_inputs) == 0 or option_and_inputs[0] not in action.options:
            self.speak(channel, action.init_response)
            self.speak(channel, '\nMake sure you delimit the commands with spaces')
        else:
            option = option_and_inputs[0]
            inputs = option_and_inputs[1:]
            try:
                action.options[option](*inputs)
            except BadInputError, e:
                self.speak(channel, str(e))

    def timed_process(self, time):
        """ Runs some commands every few seconds

        Parameters
        ----------
        time : int
            Current time
        """
        for (action, option, inputs, interval), last_time in self.timed_actions.iteritems():
            if time - last_time > interval:
                #FIXME:
                # try:
                action(*inputs)
                self.timed_actions[(action, option, inputs, interval)] = time
                # except:
                #     self.speak(some_channel, 'something went wrong with this action')
