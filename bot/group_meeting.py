from . import action

class GroupMeeting(action.Action):
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
        error_msg = ''
        if criteria in ['', 'help'] and job == '':
           error_msg += 'I will help you select members for the group meeting.\n'
        if criteria not in ['random', 'volunteer', 'myself as']:
            error_msg += ('First option controls how the job will be assigned.'
                          ' It must be one of "random", "volunteer" or "myself as".\n')
        if job not in ['presenter', 'chair']:
            error_msg += ('Second option controls the job that will be assigned.'
                          ' It must be one of "presenter" or "chair".\n')
        if error_msg != '':
            raise action.BadInputError(error_msg)

    def modify(self, item='', to_val='', *identifiers):
        error_msg = ''
        if item == '' and to_val == '' and len(identifiers) == 0:
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
        error_msg = ''
        if item == '' and to_val == '' and len(identifiers) == 0:
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
