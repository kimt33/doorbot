from . import ear
from . import mouth
from . import action

actions = ['backup', 'group meeting', 'money']

class Brain(object):
    def __init__(self, bot_id, slack_client):
        self.bot_id = bot_id
        self.slack_client = slack_client
        self.actions = [action.Action()]

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
        message : str
            Direct message that contains the command
        channel : str
            Channel from which the message arrived

        Returns
        -------
        """
        sel_actions = [(action, action.name) for action in self.actions if action.name in command]
        if len(sel_actions) > 1:
            self.speak(channel, 'I can only handle one command.')
        action, action_name = sel_actions[0]
        option_and_inputs = command.split(action_name)[1].split()
        option = option_and_inputs[0]
        inputs = option_and_inputs[1:]
        if option not in action.options:
            self.speak(channel, action.init_response)
            self.speak(channel, '\nMake sure you delimit the commands with spaces')
        else:
            try:
                action.options[option](*inputs)
            except action.BadInputError, e:
                self.speak(channel, str(e))
