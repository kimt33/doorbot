import time
from . import action

class TimedAction(action.Action):
    @property
    def name(self):
        return 'timing actions'

    @property
    def init_response(self):
        return 'response to inadequate option'

    @property
    def options(self):
        return {'add' : self.add,
                'remove' : self.remove}

    def recount(self):
        msg = 'Here are the registered timed actions:\n'
        for (action, inputs, interval), last_time in self.actor.timed_actions.iteritems():
            msg += 'Action: {0}\nInputs: {1}\n:Time Interval: {2}\n\n'
        # lazy
        raise action.BadInputError(msg)

    def add(self, *commands):
        error_msg = ''
        if len(commands) == 0 or commands[0] == '':
           error_msg += 'I will help you add timed actions.\n'
        try:
            int(commands[0])
        except ValueError:
            error_msg += ('First option specifies how often the action is repeated.'
                          ' It must be a number.\n')
        if commands[1] not in (i.name for i in self.actor.actions):
            error_msg += ('Second option specifies what is done.'
                          ' It must be one of {0}}.\n'.format(self.actor.actions.keys()))
        if error_msg != '':
            raise action.BadInputError(error_msg)
        interval = int(commands[0])
        action = self.actor.actions[commands[1]]
        option = commands[2]
        inputs = commands[3:]
        self.actor.timed_actions[(action, option, inputs, interval)] = time.time()

    def remove(self, *commands):
        error_msg = ''
        if len(commands) == 0 or commands[0] == '':
           error_msg += 'I will help you manage timed actions.\n'
        # first
        if commands[0] not in (i.name for i in self.actor.actions):
            error_msg += ('First option specifies what is done.'
                          ' It must be one of {0}}.\n'.format(self.actor.actions.keys()))
        if error_msg != '':
            raise action.BadInputError(error_msg)

