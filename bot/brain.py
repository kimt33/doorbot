""" Brain of the bot

Responsible for processing commands that are received, and for acting and responding
appropriately

"""

from . import ear
from . import mouth
from .action import BadInputError
from .timed_action import TimedAction
from .group_meeting import GroupMeeting

class Brain(object):
    """ Brain of bot

    Attribute
    ---------
    bot_id : str
        User name of bot within Slack client
    slack_client : slack.SlackClient
        Slack client within which bot lives
    actions : dict
        Dictionary of action names to instances of Action
    timed_actions : dict
        Dictionary of (instance of Action, option, inputs, interval) to last time
        process has run
        Stores processes that will be repeated in some time interval

    """
    def __init__(self, bot_id, slack_client):
        self.bot_id = bot_id
        self.slack_client = slack_client
        self.actions = {i.name:i for i in [GroupMeeting(self),
                                           TimedAction(self)]}
        self.timed_actions = {}
        # TODO: add status channel, conversation per channel (who, what, for how long)

    @property
    def call_name(self):
        """ Name of bot as it appears in Slack client
        
        """
        return "<@{0}>".format(self.bot_id)

    def listen(self, slack_rtm_output):
        """ Retrieves information from Slack client

        Parameters
        ----------
        slack_rtm_output : list of dict
            Real time output from Slack client

        Returns
        -------
        channel : str
            Channel from which the message arrived
        message : str
            Direct message
        """
        return ear.listen(self, slack_rtm_output, sound_type='dm')

    def speak(self, channel, response):
        """ Sends information to Slack client

        Parameters
        ----------
        channel : str
        Name of channel stored in Slack client
        response : str
            What bot will say on channel

        """
        mouth.speak(self, channel, response)

    def process(self, channel, command):
        """ Processes the command

        Parameters
        ----------
        channel : str
            Channel from which message received
        command : str
            Direct message that contains the command
        """
        # find actions in command
        sel_actions = [name for name in self.actions if name in command]
        if len(sel_actions) == 0:
            self.speak(channel, 'I can only do one of {0}.'.format(self.actions.keys()))
        # reorder actions
        sel_actions = sorted(sel_actions, key=command.index)

        action_name = sel_actions[0]
        action = self.actions[action_name]
        # separate options
        option_and_inputs = command.split(action_name)[1].split()

        if len(option_and_inputs) == 0 or option_and_inputs[0] not in action.options:
            self.speak(channel, self.actions[action_name].init_response)
            self.speak(channel, '\nMake sure you delimit the commands with spaces')
        else:
            # run process
            option = option_and_inputs[0]
            inputs = option_and_inputs[1:]
            try:
                action.options[option](*inputs)
                self.speak(channel, 'Done!')
            except BadInputError, e:
                self.speak(channel, str(e))

    def timed_process(self, time):
        """ Runs stored commands every few seconds

        Parameters
        ----------
        time : int
            Current time
        """
        for (action, option, inputs, interval), last_time in self.timed_actions.iteritems():
            if time - last_time > interval:
                #FIXME:
                # try:
                action.options[option](*inputs)
                self.timed_actions[(action, option, inputs, interval)] = time
                # except:
                #     self.speak(some_channel, 'something went wrong with this action')
                # self.speak(channel, 'Done!')
