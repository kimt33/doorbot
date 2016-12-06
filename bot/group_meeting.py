""" Module for interfacing group meeting code with bot

Takes commands from Slack client and translate them into script

"""
from . import action

class GroupMeeting(action.Action):
    """ Action class for group meeting management
    """
    @property
    def name(self):
        return 'group meeting'

    @property
    def init_response(self):
        return ('I can only do one of {0}'
                ' when managing group meetings').format(self.options.keys())

    @property
    def options(self):
        return {'select' : self.select_member,
                'modify' : self.modify,
                'recount' : self.recount}

    def select_member(self, criteria='', job=''):
        """ Selects member

        Parameters
        ----------
        criteria : str
            How each member is selected
            One of ['random', 'volunteer', 'myself as']
        job : str
            What role is being selected
            One of ['presenter', 'chair]
        """
        error_msg = ''
        if criteria in ['', 'help'] and job == '':
           error_msg += 'I will help you select members for the group meeting.\n'
        if criteria not in ['random', 'volunteer', 'myself']:
            error_msg += ('First option controls how the job will be assigned.'
                          ' It must be one of "random", "volunteer" or "myself".\n')
        if job not in ['presenter', 'chair']:
            error_msg += ('Second option controls the job that will be assigned.'
                          ' It must be one of "presenter" or "chair".\n')
        if error_msg != '':
            raise action.BadInputError(error_msg)

    def modify(self, item='', to_val='', *identifiers):
        """ Modifies existing presentation information

        Parameters
        ----------
        item : str
            Parameter that will be modified
            One of ['presenter', 'chair', 'title', 'date']
        to_val : str
            Value to which it will be changed
        identifiers : list
            Identifier of the presentation that will be modified
            Each entry is string where ':' delimits the identifier from value
            e.g. ['presenter:name', 'chair:name']

        """
        error_msg = ''
        if item == '' or to_val == '' or len(identifiers) == 0:
           error_msg += 'I will help you modify a group meeting.\n'
        if item not in ['presenter', 'chair', 'title', 'date']:
            error_msg += ('First option controls what is being modified.'
                          ' It must be one of "presenter", "chair", "title", or "date".\n')
        if to_val == '':
            error_msg += ('Second option is the value to which the item will be changed.\n')
        for i in identifiers:
            if i.split(':')[0] not in ['presenter', 'chair', 'title', 'date']:
                error_msg += ('Third option onwards are the identifiers of the presentation'
                              ' that will be modified.'
                              ' Each identifier must be one of "presenter", "chair", "title", or "date".'
                              ' The value of each identifier is delimited by ":".'
                              ' For example, "presenter:person1 chair:person2"\n')
                break
        else:
            identifiers = {i:j for i,j in identifier.split(':') for identifier in identifiers}
        if error_msg != '':
            raise action.BadInputError(error_msg)

    def recount(self, *identifiers):
        """ Shows all presentations that satifies some conditions

        Parameters
        ----------
        identifiers : list
            Identifier of the presentations
            Each entry is string where ':' delimits the identifier from value
            e.g. ['presenter:name', 'chair:name']

        """
        error_msg = ''
        if len(identifiers) == 0:
           error_msg += 'I will help you recount information on a group meeting.\n'
        for i in identifiers:
            if i.split(':')[0] not in ['presenter', 'chair', 'title', 'date']:
                error_msg += ('All given options are the identifiers of a particular presentation.'
                              ' Each identifier must be one of "presenter", "chair", "title", or "date".'
                              ' The value of each identifier is delimited by ":".'
                              ' For example, "presenter:person1 chair:person2"\n')
                break
        else:
            identifiers = {i:j for i,j in identifier.split(':') for identifier in identifiers}
        if error_msg != '':
            raise action.BadInputError(error_msg)


