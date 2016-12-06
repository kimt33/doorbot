import time
from .action import Action, BadInputError

class TimedAction(Action):
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
        msg = 'Here are the registered timed actions:\n'
        for (action, option, inputs, interval), last_time in self.actor.timed_actions.iteritems():
            msg += ('Command: {0} {1} {2}\n'
                    'Time Interval: {3}\n'
                    'Last Time: {4}\n'.format(action.name, option, inputs, interval, last_time))
        # lazy
        raise BadInputError(msg)

    def add(self, interval=0, action='', *commands):
        error_msg = ''
        if interval == 0 or action == '' or len(commands) == 0:
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
            raise BadInputError(error_msg)
        action = self.actor.actions[action]
        option = commands[0]
        inputs = commands[1:]
        action.options[option](*inputs)
        self.actor.timed_actions[(action, option, inputs, interval)] = time.time()

    def remove(self, *commands):
        error_msg = ''
        if len(commands) == 0 or commands[0] == '':
            error_msg += 'I will help you manage timed actions.\n'
            error_msg += ('Repeat the command that you would like to remove.'
                          ' See `@ayerslab_bot timing actions recount` for a list of commands')
        if error_msg != '':
            raise BadInputError(error_msg)

    #TODO: modify
