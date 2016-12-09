""" Module for interfacing group member database with bot

Takes commands from Slack client and translate them into script

"""
import re
import sqlite3
from datetime import datetime, date
from . import action

class GroupMember(action.Action):
    """ Action class for group member management
    """
    def __init__(self, actor, db='members.db'):
        """
        Parameters
        ----------
        actor : Brain
            Brain instance that describes the acting bot
        db : str
            Name of the database file
        """
        super(GroupMember, self).__init__(actor)
        self.db_conn = sqlite3.connect(db)
        self.cursor = self.db_conn.cursor()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        if u'members' not in (j for i in self.cursor.fetchall() for j in i):
            self.cursor.execute('''CREATE TABLE members
            (name text, slack_id text, email text, position text, dates_away text)''')
            self.db_conn.commit()

    @property
    def name(self):
        return 'members'

    @property
    def init_response(self):
        return ('I can only do one of {0}'
                ' when managing group members').format(self.options.keys())

    @property
    def options(self):
        return {'add' : self.add, 'list':self.list}

    def add(self, name='', slack_id='', email='', position='', is_present=''):
        if name == '':
            raise action.BadInputError('What is their name?')
        if slack_id == '':
            raise action.BadInputError("What is their Slack ID? If you don't know,"
                                       " just reference using `@`, for example,"
                                       " @ayerslab_bot.\n"
                                       "If they don't have Slack or you don't know,"
                                       " just write `N/A`",
                                       args=(name,))
        if email == '':
            raise action.BadInputError('What is their email address?',
                                       args=(name, slack_id))
        if position == '' or position not in ['undergrad', 'Master\'s',
                                              'PhD', 'Postdoc', 'Professor']:
            raise action.BadInputError('What is their role in the group? It should'
                                       ' be one of "undergrad", "Master\'s",'
                                       ' "PhD", "Postdoc", or "Professor".',
                                       args=(name, slack_id, email))
        if is_present == '' or is_present not in ['yes', 'no']:
            raise action.BadInputError('Are they in the lab? It should be one of "yes" or "no".',
                                       args=(name, slack_id, email, position))
        if is_present == 'no':
            dates_present = '(9999-12-31:{0})'.format(date.today().isoformat())
        elif is_present == 'yes':
            dates_present = ''

        self.cursor.execute('INSERT INTO members VALUES (?,?,?,?,?)',
                            (name, slack_id, email, position, dates_present))
        self.db_conn.commit()

    def modify(self, name='', to_val='', *identifiers):
        if len(identifiers) == 0:
            raise action.BadInputError('Whose data would you like to change?')
        self.cursor.execute('SELECT * FROM members WHERE name=?', name)
        self.cursor.fetchall()

    def list(self):
        message = '{0}{1:>15s}{2:>15s}{3:>15}{4:>15}\n'.format('Name', 'Slack ID', 'Email', 'Who?', 'Away?')
        for row in self.cursor.execute('SELECT * FROM members ORDER BY dates_present'):
            # find dates
            dates = re.findall(r'\d\d\d\d-\d\d-\d\d', row[-1])
            to_dates = dates[0::2]
            from_dates = dates[1::2]
            is_away = 'no'
            for to_date, from_date in zip(to_dates, from_dates):
                if from_date <= date.today() < to_date:
                    is_away = 'yes'
                    break
            # construct message
            data = row[:-1] + tuple(is_away)
            message += '{0}{1:>15s}{2:>15}{3:>15}{4:>15}\n'.format(*data)
        raise action.BadInputError(message)

    def import_from_slack(self):
        pass

