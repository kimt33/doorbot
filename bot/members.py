""" Module for interfacing group member database with bot

Takes commands from Slack client and translate them into script

"""
import re
from datetime import datetime, date
from .action import Action
from .brain import BadInput, Messaging

class GroupMember(Action):
    """ Action class for group member management
    """
    def __init__(self, db_conn):
        """
        Parameters
        ----------
        db_conn : sqlite3.Connection
            Database object
        """
        self.db_conn = db_conn
        self.cursor = self.db_conn.cursor()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        if u'members' not in (j for i in self.cursor.fetchall() for j in i):
            self.cursor.execute('''CREATE TABLE members
            (id INTEGER PRIMARY KEY,
             name TEXT,
             userid TEXT NOT NULL,
             slack_id TEXT,
             email TEXT,
             role TEXT,
             dates_away TEXT,
             permission TEXT)''')
            self.db_conn.commit()
        # FIXME: there hsould be a better way for this
        self.col_ids = {'id':0,
                        'name':1,
                        'userid':2,
                        'slack_id':3,
                        'email':4,
                        'role':5,
                        'dates_away':6,
                        'permission':7}

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
                'import':self.import_from_slack, 'away':self.add_away}

    @property
    def valid_roles(self):
        return ['undergrad', 'Master\'s', 'PhD', 'Postdoc', 'Professor']

    def is_valid_role(self, role):
        if role in self.valid_roles:
            return True
        else:
            return False

    def _find_from_identifiers(self, *identifiers):
        where_command = 'WHERE '
        vals = []
        for identifier in identifiers:
            key, val = identifier.split('=')
            where_command += '{0}=? '.format(key)
            vals.append(val)

        self.cursor.execute('SELECT * FROM members {0} '.format(where_command), vals)
        rows = self.cursor.fetchall()
        if len(rows) == 0:
            return '', None, 0
        elif len(rows) > 1:
            return '', None, 2
        else:
            return where_command, vals, rows[0]

    def add(self, name='', userid='', slack_id='', email='', role='', is_away='', permission=''):
        if name == '':
            raise BadInput('What is their name?')
        if userid == '':
            raise BadInput("What is their Slack username?"
                                       " If you don't know, just write `None`.",
                                       args=(name,))
        if slack_id == '':
            raise BadInput("What is their Slack ID?"
                                       " If you don't know, just write `None`",
                                       args=(name, userid))
        if email == '':
            raise BadInput('What is their email address?',
                                       args=(name, userid, slack_id))

        if not self.is_valid_role(role):
            raise BadInput('What is their role in the group?'
                                       ' It should be one of {0}.'.format(self.valid_roles),
                                       args=(name, userid, slack_id, email))
        if is_away == '' or is_away not in ['yes', 'no']:
            raise BadInput('Are they away from the lab? It should be one of "yes" or "no".',
                                       args=(name, userid, slack_id, email, role))
        dates_away = ''
        if is_away == 'yes':
            dates_away = '({0}:{1})'.format(date.max, date.today())
        elif is_away == 'no':
            dates_away = ''

        permission = 'user'

        if userid == 'None':
            userid = ''
        if slack_id == 'None':
            slack_id = ''

        self.cursor.execute('INSERT INTO members'
                            ' (name, userid, slack_id, email, role, dates_away, permission)'
                            ' VALUES (?,?,?,?,?,?,?)',
                            (name, userid, slack_id, email, role, dates_away, permission))
        self.db_conn.commit()

    def add_away(self, from_date='', to_date='', *identifiers):
        try:
            if from_date in ['NA', 'N/A']:
                from_date = date.today()
            else:
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        except ValueError:
            raise BadInput('From what date will this person be away?'
                                       ' You should give the date in the form yyyy-mm-dd.'
                                       " If you don't know the exact date, say `N/A`.")
        try:
            if to_date in ['NA', 'N/A']:
                to_date = datetime.max.date()
            else:
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
        except ValueError:
            raise BadInput('To what date will this person be away?'
                                       " If you don't know the exact date, say `N/A`",
                                       args=(str(from_date),))

        if from_date > to_date:
            raise Messaging("I can't understand the dates you've given."
                                   " You will be away from {0} to {1}?"
                                   " Please try again.".format(from_date,
                                                               to_date))
        if len(identifiers) == 0:
            raise BadInput('Who is this person?'
                                       ' Could you tell me the one or more of {0}?'
                                       ' And could you delimit the value with `=`?'
                                       ' For example, `name=ayersbot`.'.format(self.col_ids.keys()),
                                       args=(str(from_date), str(to_date)))

        where_command, vals, row = self._find_from_identifiers(*identifiers)
        if where_command == '' and row == 0:
            raise BadInput('I could not find anyone using {0}'.format(identifiers))
        elif where_command == '' and row == 1:
            raise BadInput('There seems to be more than one person that'
                                       ' satisfies {0}. Could you give more information'
                                       ' on the person?'.format(identifiers),
                                       args=(str(from_date), str(to_date)) + tuple(identifiers))

        old_dates = re.findall(r'\d\d\d\d-\d\d-\d\d', row[self.col_ids['dates_away']])
        old_dates = [datetime.strptime(i, '%Y-%m-%d').date() for i in old_dates]

        old_to_dates = old_dates[0::2]
        old_from_dates = old_dates[0::1]
        old_dates = sorted(zip(old_to_dates, old_from_dates), key=lambda x:x[0])

        new_dates = []
        for old_to_date, old_from_date in old_dates:
            if old_from_date == from_date <= to_date < old_to_date == date.max:
                new_dates.append('({0},{1})'.format(to_date, from_date))
            elif from_date <= to_date < old_from_date <= old_to_date:
                new_dates.append('({0},{1})'.format(to_date, from_date))
                new_dates.append('({0},{1})'.format(old_to_date, old_from_date))
            elif old_from_date <= old_to_date < from_date <= to_date:
                new_dates.append('({0},{1})'.format(old_to_date, old_from_date))
                new_dates.append('({0},{1})'.format(to_date, from_date))
            else:
                raise Messaging('The dates you have given overlaps'
                                       ' with the dates already recorded')
        if len(old_dates) == 0:
            new_dates.append('({0},{1})'.format(to_date, from_date))

        self.cursor.execute('UPDATE members SET {0}=? {1}'.format('dates_away', where_command),
                            [','.join(new_dates),] + vals)
        self.db_conn.commit()

    def modify(self, item='', to_val='', *identifiers):
        if item == '' or item not in self.col_ids.keys():
            raise BadInput('What would you like to change? It should be'
                                       ' one of {0}'.format(self.col_ids.keys()))
        if to_val == '':
            raise BadInput('What would you like to change it to?',
                                       args=(item,))

        if item == 'role' and self.is_valid_role(to_val):
            raise BadInput('The role must be one of {0}'.format(self.valid_roles),
                                       args=(item,))

        if len(identifiers) == 0:
            raise BadInput('Can you tell me more about this person?'
                                       ' Could you tell me the one or more of {0}}?'
                                       ' And could you delimit the value with `=`?'
                                       ' For example, `name=ayersbot`.'.format(self.col_ids.keys()),
                                       args=(item, to_val))

        where_command, vals, row = self._find_from_identifiers(*identifiers)
        if where_command == '' and row == 0:
            raise BadInput('I could not find anyone using {0}'.format(identifiers))
        elif where_command == '' and row == 1:
            raise BadInput('There seems to be more than one person that'
                                       ' satisfies {0}. Could you give more information'
                                       ' on the person?'.format(identifiers),
                                       args=(item, to_val) + tuple(identifiers))
        else:
            self.cursor.execute('UPDATE members SET {0}=? {1}'.format(item, where_command),
                                [to_val,]+vals)
            self.db_conn.commit()

    def list(self, *column_identifiers):
        col_names =  {'id':'Database ID',
                      'name':'Name',
                      'userid':'User ID',
                      'slack_id':'Slack ID',
                      'email':'Email',
                      'role':'Role',
                      'dates_away':'Dates Away',
                      'is_away':'Away?',
                      'permission':'Permission'}
        col_formats = {'id':'{:<4}',
                       'name':'{:<30}',
                       'userid':'{:<10}',
                       'slack_id':'{:<20}',
                       'email':'{:<40}',
                       'role':'{:<20}',
                       'dates_away':'{:<15}',
                       'is_away':'{:<15}',
                       'permission':'{:<12}'}

        if len(column_identifiers) == 0:
            # column_identifiers = ['id', 'name', 'userid', 'email', 'role', 'is_away', 'permission']
            column_identifiers = ['id', 'name', 'userid', 'slack_id', 'email', 'role', 'dates_away', 'is_away', 'permission']

        message_format = u''.join(col_formats[i] for i in column_identifiers) + u'\n'
        message = message_format.format(*[col_names[i] for i in column_identifiers])

        for row in self.cursor.execute('SELECT * FROM members ORDER BY dates_away'):
            row_data = []
            for identifier in column_identifiers:
                # find dates
                if identifier == 'is_away':
                    dates = re.findall(r'\d\d\d\d-\d\d-\d\d', row[self.col_ids['dates_away']])
                    to_dates = dates[0::2]
                    from_dates = dates[1::2]
                    is_away = 'no'
                    for to_date, from_date in zip(to_dates, from_dates):
                        to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
                        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                        if from_date <= date.today() < to_date:
                            is_away = 'yes'
                            break
                    row_data.append(is_away)
                else:
                    index = self.col_ids[identifier]
                    row_data.append(row[index])
            # construct message
            message += message_format.format(*row_data)
        raise Messaging(message)

    def import_from_slack(self):
        names = []
        userids = []
        slack_ids = []
        emails = []
        roles = []
        away_dates = []
        permissions = []
        def check(profile, text):
            try:
                return profile[text]
            except KeyError:
                return ''
        for i in self.actor.slack_client.api_call('users.list')['members']:
            # check if already in database
            self.cursor.execute("SELECT rowid FROM members WHERE userid = ?", (i['name'],))
            if self.cursor.fetchone():
                continue

            names.append(check(i['profile'], 'real_name'))
            userids.append(i['name'])
            slack_ids.append(i['id'])
            emails.append(check(i['profile'], 'email'))
            roles.append('')
            if 'status' not in i:
                away_dates.append('({0}:{1})'.format(date.max, date.today()))
            else:
                away_dates.append('')
            permissions.append('user')
        self.cursor.executemany("""INSERT INTO members
                                (name, userid, slack_id, email, role, dates_away, permission)
                                VALUES (?,?,?,?,?,?,?)""",
                                zip(names, userids, slack_ids, emails, roles, away_dates, permissions))
        self.db_conn.commit()
