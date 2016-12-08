""" Module for interfacing group member database with bot

Takes commands from Slack client and translate them into script

"""
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
            (name text, slack_id text, email text, position text, dates_present text)''')
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
                                       " just write `N/A`")
        if email == '':
            raise action.BadInputError('What is their email address?')
        if position == '' or position not in ['undergrad student', 'Master\'s student',
                                              'PhD student', 'Postdoc', 'Professor']:
            raise action.BadInputError('What is their role in the group? It should'
                                       ' be one of "undergrad student", "Master\'s student",'
                                       ' "PhD student", "Postdoc", or "Professor".')
        if is_present == '' or is_present not in ['yes', 'no']:
            raise action.BadInputError('Are they in the lab? It should be one of "yes" or "no".')
        if is_present == 'yes':
            dates_present = '(9999-99-99:{0})'.format(date.today().isoformat())
        elif is_present == 'no':
            dates_present = ''

        self.cursor.execute('INSERT INTO members VALUES (%s,%s,%s,%s,%s)',
                            name, slack_id, email, position, dates_present)
        self.db_conn.commit()

    def modify(self, item='', to_val='', *identifiers):
        if len(identifiers) == 0:
            raise action.BadInputError('Whose data would you like to change?')

    def list(self):
        message = '{0}{1:>15s}{2:>15s}{3:>15}{4:>15}'.format('Name', 'Slack ID', 'Email', 'Who?', 'Away?')
        for row in self.cursor.execute('SELECT * FROM members ORDER BY dates_present'):
            message += '{0}{1:>15s}{2:>15}{3:>15}'.format(*row)
        raise action.BadInputError(message)

    def import_from_slack(self):
        pass

