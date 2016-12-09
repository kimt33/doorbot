""" Module for interfacing group meeting code with bot

Takes commands from Slack client and translate them into script

"""
import datetime
import sqlite3
from . import action

class GroupMeeting(action.Action):
    """ Action class for group meeting management
    """
    def __init__(self, actor, db='groupmeetings.db'):
        """
        Parameters
        ----------
        actor : Brain
            Brain instance that describes the acting bot
        db : str
            Name of the database file
        """
        super(GroupMeeting, self).__init__(actor)
        self.db_conn = sqlite3.connect(db)
        self.cursor = self.db_conn.cursor()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        if u'group_meetings' not in (j for i in self.cursor.fetchall() for j in i):
            self.cursor.execute('''CREATE TABLE group_meetings
            (date text, presenter text, chair text, title text)''')
            self.db_conn.commit()

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

    def select_member(self, criteria='', job='', date=''):
        """ Selects member

        Parameters
        ----------
        criteria : str
            How each member is selected
            One of ['random', 'volunteer', 'myself as']
        job : str
            What role is being selected
            One of ['presenter', 'chair]
        date : str
            Date of presentation
            'next' or 'yyyy/mm/dd'
        """
        error_msg = ''
        if criteria not in ['random', 'volunteer', 'myself']:
            raise action.BadInputError('First option controls how the job will be assigned.'
                                       ' It must be one of "random", "volunteer" or "myself".\n')
        if job not in ['presenter', 'chair']:
            raise action.BadInputError('Second option controls the job that will be assigned.'
                                       ' It must be one of "presenter" or "chair".\n',
                                       args=(criteria,))
        if date == 'next':
            # FIXME:
            pass
        else:
            try:
                year, month, day = [int(i) for i in date.split('-')]
            except (ValueError, TypeError):
                error_msg += ('Third option controls the date of the presentation.'
                              ' It must be one of "next" or "yyyy-mm-dd".\n')
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


    def get_weights(self, date, weight_type='presenter'):
        """ Assigns weights for the weighed probability distribution

        Parameters
        ----------
        date : datetime.date
        weight_type : {'presenter', 'chair'}
            'presentation' gives weights for the presenter
            'chair' gives weights for the chair

        Returns
        -------
        weights
            weights for each person

        Raises
        ------
        AssertionError
            If weight_type is not 'presenter' or 'chair'
        """
        if weight_type not in ['presenter', 'chair']:
            raise ValueError('Given weight_type is not supported')
        weeks_since = []
        for person in self._presenters:
            if (not person.is_away(date) and 
                person.position not in ['undergrad', 'visiting', 'professor']):
                if weight_type == 'presenter':
                    dates_past = person.dates_presented +\
                                 [i for i in person.dates_to_present if i<date]
                elif weight_type == 'chair':
                    dates_past = person.dates_chaired +\
                                 [i for i in person.dates_to_chair if i<date]
                num_weeks = datetime.timedelta(days=15)
                if len(dates_past) != 0:
                    num_weeks = min((date-dates_past[-1])/7, num_weeks)
                weeks_since.append(num_weeks.days)
            else:
                weeks_since.append(0.)
        weights = [i if i>3 else 0. for i in weeks_since]
        return weights


