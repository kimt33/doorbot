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
            (name text, slack_id text, email text, position text, dates_away text, permission text)''')
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
        return {'add':self.add, 'list':self.list, 'modify':self.modify,
                'import':self.import_from_slack}

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
                                       ' be one of "undergrad", "Master\'s student",'
                                       ' "PhD student", "Postdoc", or "Professor".',
                                       args=(name, slack_id, email))
        if is_present == '' or is_present not in ['yes', 'no']:
            raise action.BadInputError('Are they in the lab? It should be one of "yes" or "no".',
                                       args=(name, slack_id, email, position))
        if is_present == 'no':
            dates_away = '(9999-12-31:{0})'.format(date.today().isoformat())
        elif is_present == 'yes':
            dates_away = ''

        self.cursor.execute('INSERT INTO members VALUES (?,?,?,?,?,?)',
                            (name, slack_id, email, position, dates_away, 'user'))
        self.db_conn.commit()

    def modify(self, item='', to_val='', *identifiers):
        if item == '' or item not in ['name', 'slack_id', 'email', 'position', 'dates_away']:
            raise action.BadInputError('What would you like to change? It should be'
                                       ' one of {0}'.format(['name', 'slack_id', 'email',
                                                             'position', 'dates_away']))
        if to_val == '':
            raise action.BadInputError('What would you like to change it to?',
                                       args=(item,))
        if len(identifiers) == 0:
            raise action.BadInputError('Can you tell me more about this person?'
                                       ' Could you tell me the name, slack id, email'
                                       ' or position?'
                                       ' And could you delimit the value with `=`?'
                                       ' For example, `name=ayersbot`.',
                                       args=(item, to_val))

        where_command = ' WHERE '
        vals = []
        for identifier in identifiers:
            key, val = identifier.split('=')
            where_command += '{0}=? '.format(key)
            vals.append(val)

        self.cursor.execute('SELECT * FROM members'+where_command, vals)
        rows = self.cursor.fetchall()
        if len(rows) == 0:
            raise action.BadInputError('I could not find anyone using {0}'.format(identifiers))
        elif len(rows) > 1:
            raise action.BadInputError('There seems to be more than one person that'
                                       ' satisfies {0}. Could you give more information'
                                       ' on the person?'.format(identifiers),
                                       args=(item, to_val) + tuple(identifiers))
        # update table
        self.cursor.execute('UPDATE members SET {0}=?'.format(item)+where_command,
                            [to_val,]+vals)
        self.db_conn.commit()

    def list(self):
        message = '{0:<30s}{1:>40s}{2:>20}{3:>15}\n'.format('Name', 'Email', 'Who?', 'Away?')
        for row in self.cursor.execute('SELECT * FROM members ORDER BY dates_away'):
            # find dates
            dates = re.findall(r'\d\d\d\d-\d\d-\d\d', row[-2])
            to_dates = dates[0::2]
            from_dates = dates[1::2]
            is_away = 'no'
            for to_date, from_date in zip(to_dates, from_dates):
                to_date = datetime.strptime(to_date, '%Y-%m-%d')
                from_date = datetime.strptime(from_date, '%Y-%m-%d')
                if from_date <= datetime.today() < to_date:
                    is_away = 'yes'
                    break
            # construct message
            data = row[0:1] + row[2:-2] + (is_away,)
            message += u'{0:<30s}{1:>40}{2:>20}{3:>15}\n'.format(*data)
        print message
        raise action.Messaging(message)

    def import_from_slack(self):
        names = []
        slack_ids = []
        emails = []
        positions = []
        away_dates = []
        permissions = []
        def check(profile, text, else_val=''):
            try:
                if not profile[text]:
                    raise KeyError
                return profile[text]
            except KeyError:
                return else_val
        for i in self.actor.slack_client.api_call('users.list')['members']:
            names.append(check(i['profile'], 'real_name', i['name']))
            slack_ids.append(i['id'])
            emails.append(check(i['profile'],'email'))
            positions.append('')
            if 'status' not in i:
                away_dates.append('(9999-12-31:{0})'.format(date.today().isoformat()))
            else:
                away_dates.append('')
            permissions.append('user')
        self.cursor.executemany('INSERT INTO members VALUES (?,?,?,?,?,?)',
                            zip(names, slack_ids, emails, positions, away_dates, permissions))
        self.db_conn.commit()

