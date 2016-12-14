""" Brain of the bot

Responsible for processing commands that are received, and for acting and responding
appropriately

"""
import shlex
import sqlite3
from . import ear
from . import mouth
from .action import BadInput, Messaging
from .timed_action import TimedAction
from .members import GroupMember
from .group_meeting import GroupMeeting
from .utils import nice_options

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
    commands : dict
        Dictionary of channel to (userid, last input, time)

    """
    def __init__(self, bot_id, slack_client, status_channel):
        self.bot_id = bot_id
        self.slack_client = slack_client
        self.db_conn = sqlite3.connect('ayerslab.db')
        self.cursor = self.db_conn.cursor()
        self.actions = {i.name:i for i in [GroupMember(self, self.db_conn),
                                           TimedAction(self),
                                           GroupMeeting(self.db_conn),]}
        self.timed_actions = {}
        self.commands = {}
        self.conversations = {}
        self.status_channel = status_channel

    @property
    def call_name(self):
        """ Name of bot as it appears in Slack client

        """
        return "<@{0}>".format(self.bot_id)

    def listen(self, slack_rtm_output, sound_type='all'):
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
        return ear.listen(self, slack_rtm_output, sound_type=sound_type)

    def speak(self, channel, response, dm=''):
        """ Sends information to Slack client

        Parameters
        ----------
        channel : str
            Name of channel stored in Slack client
        response : str
            What bot will say on channel

        """
        mouth.speak(self, channel, response, dm=dm)

    def _process_step1(self, command):
        """ Checks to see if given command uses provides an allowed action
        """
        sel_actions = [name for name in self.actions if name in command]
        if len(sel_actions) == 0:
            message = ('I can only do one of {0}.'
                       ''.format(nice_options(self.actions.keys())))
            return (False, message)
        # reorder actions
        sel_actions = sorted(sel_actions, key=command.index)
        return (True, sel_actions[0])

    def _process_step2(self, action, command):
        """ Checks if the option corresponds with the action
        """
        options = [i for i in action.options if i in command]
        if len(options) == 0:
            message = action.init_response
            return (False, message)
        elif len(options) >= 2:
            message = 'I have more than one valid options.'
            message += '\nPlease give me only one of {0}.'.format(action.options)
            return (False, message)
        return (True, options[0])

    def process(self, channel, command, user='', time=0, dm=False):
        """ Processes the command

        Responds to commands initiated by a direct message

        Parameters
        ----------
        channel : str
            Channel from which message received
        command : str
            Direct message that contains the command
        user : str
            Who is messaging
        time : int
            What time they messaged
        dm : bool
            True if message is explicitly directed at bot
            False if message is not explicitly directed at bot
        """
        # FIXME: doesn't work with timed action

        time = float(time)
        # skip commands that are not directed at bot (unless already in conversation)
        if (not dm and (channel not in self.commands or
                        self.commands[channel][0] != user)):
            return
        # make conversation
        if (channel not in self.commands or
                abs(time - self.commands[channel][1]) > 60):
            self.commands[channel] = (user, time)
        # can only converse with one person per channel
        elif self.commands[channel][0] != user:
            self.speak(channel,
                       "I'm sorry, I'm currently talking with <@{0}> at the moment."
                       "".format(self.commands[channel][0]),
                       dm=user)
            return
        # end conversation
        enders = ['forget', 'reset', 'fuck', 'shut up', 'stop', 'forget', 'bye']
        for ender in enders:
            if ender in command:
                del self.commands[channel]
                self.speak(channel, 'Alright then.', dm=user)
                return
        # check
        if 'status' in command:
            self.speak(channel,
                       'Bleep bloop\n{0}'.format(' '.join(self.commands[channel][2:])),
                       dm=user)
            return
        # undo
        if 'undo' in command:
            self.speak(channel, 'Undoing the last input.')
            self.commands[channel] = self.commands[channel][:-1]
            return

        # remember old conversation
        old_conv = self.commands[channel][2:]

        # find actions in command
        action_name = ''
        if len(old_conv) >= 1:
            action_name = old_conv[0]
        else:
            step1 = self._process_step1(command)
            # if nothing found
            if not step1[0]:
                self.speak(channel, step1[1], dm=user)
                return
            action_name = step1[1]
            self.commands[channel] = (user, time, action_name)
            command = command.split(action_name, 1)[1]

        # find option in command
        action = self.actions[action_name]
        option = ''
        if len(old_conv) >= 2:
            option = old_conv[1]
        else:
            step2 = self._process_step2(action, command)
            # if nothing found
            if not step2[0]:
                self.speak(channel, step2[1], dm=user)
                return
            option = step2[1]
            command = command.split(option, 1)[1]
            self.commands[channel] = (user, time, action_name, option)

        # find parameters
        command = command.strip()
        parameters = old_conv[2:]
        if len(command) > 2 and command[0] in ["'", '"'] and command[-1] == command[0]:
            parameters += tuple(shlex.split(command[1:-1]))
        elif command != '':
            parameters += (command,)

        # act
        try:
            action.options[option](*parameters)
            self.speak(channel, 'Done!')
            del self.commands[channel]
        except BadInput as handler:
            self.speak(channel, handler.message)
            self.commands[channel] = self.commands[channel][:4] + handler.args
        except Messaging as handler:
            self.speak(channel, handler.message)
            del self.commands[channel]

    def timed_process(self, time):
        """ Runs stored commands every few seconds

        Parameters
        ----------
        time : int
            Current time
        """
        for (action, option, inputs, interval), last_time in self.timed_actions.iteritems():
            if time - last_time > interval:
                try:
                    action.options[option](*inputs)
                    self.timed_actions[(action, option, inputs, interval)] = time
                except Messaging as handler:
                    self.speak(self.status_channel, handler.message)
                except:
                    self.speak(self.status_channel,
                               'Something went terribly wrong with {0}'.format(action))

    def initiate_conv(self, channel, label, user, response, kwrds_response, time=0):
        """ Initiates conversation with users

        Parameters
        ----------
        channel : str
            Channel in which conversation occurs
        label : str
            Conversation label
        response : str
            Response from users
        user : str
            Who is messaging
        kwrd_response : dict of (tuple of str) to str
            List of words that results in a specific response
            Empty tuple is ice breaker (conversation starter)
        time : int
            What time at which conversation occurs

        Note
        ----
        Only supports one level of conversation (bot say, they say, bot say)
        """
        # if no conversation yet or in some while
        if (channel not in self.conversations or
                abs(time - self.conversations[channel][1]) > 60):
            self.conversations[channel] = (time, )
        # break ice
        if len(self.conversations[channel]) == 1:
            self.speak(channel, kwrds_response[()])
            self.conversations[channel] += (label, )
        # await response
        elif len(self.conversations[channel]) == 2:
            for kwrd, backtalk in ((kwrd, val)
                                   for kwrds, val in kwrds_response.iteritems()
                                   for kwrd in kwrds):
                if kwrd in response:
                    self.speak(channel, backtalk)
                    self.conversations[channel] += (user, response)
                    break
