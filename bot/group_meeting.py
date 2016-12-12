""" Module for interfacing group meeting code with bot

Takes commands from Slack client and translate them into script

"""
import re
from datetime import datetime, date, timedelta
from random import random
from . import action

class GroupMeeting(action.Action):
    """ Action class for group meeting management
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
        if u'group_meetings' not in (j for i in self.cursor.fetchall() for j in i):
            self.cursor.execute('''CREATE TABLE group_meetings
            (id INTEGER PRIMARY KEY,
             date TEXT NOT NULL,
             presenter INTEGER,
             chair INTEGER,
             title TEXT)''')
            self.db_conn.commit()
        # FIXME: there should be a better way for this
        self.col_ids = {'id':0,
                        'date':1,
                        'presenter':2,
                        'slack_chair':3,
                        'title':4,}

    @property
    def name(self):
        return 'group meeting'

    @property
    def init_response(self):
        return ('I can only do one of {0}'
                ' when managing group meetings').format(self.options.keys())

    @property
    def options(self):
        return {'add' : self.add,
                'recount' : self.recount}

    def is_valid_date(self, date_str):
        if date_str in ['next']:
            return True
        try:
            datetime.strptime(date_str, '%Y-%m-%d').date()
            return True
        except ValueError:
            return False

    def _find_from_identifiers(self, *identifiers):
        where_command = ''
        vals = []
        if len(identifiers) > 0:
            where_command += 'WHERE '
            keys = identifiers[0::2]
            vals = identifiers[1::2]
            for key in keys:
                where_command += '{0}=? '.format(key)

        self.cursor.execute('SELECT * FROM group_meetings {0} '.format(where_command), vals)
        rows = self.cursor.fetchall()
        return where_command, vals, rows


    def select_member_volunteer(self, job='', date_str=''):
        pass

    def select_member_random(self, date_obj, job):
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
        # find people that are present
        people_present = []
        for row in self.cursor.execute('SELECT id, name, dates_away FROM members'):
            dates = re.findall(r'\d\d\d\d-\d\d-\d\d', row[2])[:2]
            dates = [datetime.strptime(i, '%Y-%m-%d').date() for i in dates]
            to_dates = dates[0::2]
            from_dates = dates[0::1]
            for to_date, from_date in zip(to_dates, from_dates):
                if to_date < date_obj:
                    # ASSUME away_dates are in descending order
                    # there is no need to loop through all dates if a date is
                    # we find a valid date
                    people_present.append(row[0])
                    break
                elif from_date <= date_obj <= to_date:
                    # if person is away on that day, break out of loop
                    break
            else:
                # if end of for loop reached
                people_present.append(row[0])

        # find time since last presentation
        time_since_last = []
        for i in people_present:
            self.cursor.execute('SELECT * FROM group_meetings WHERE {0}=?'
                                ' ORDER BY date DESC'.format(job), (i,))
            last_date = self.cursor.fetchone()
            if last_date in [None, '']:
                last_date = datetime.min.date()
            else:
                last_date = datetime.strptime(last_date[1], '%Y-%m-%d').date()
            time_since_last.append((date_obj - last_date).days)
        time_since_last = [i if i>27 else 0 for i in time_since_last]

        # you can't present and chair at the same time
        other = ''
        if job == 'presenter':
            other = 'chair'
        elif job == 'chair':
            other = 'presenter'
        self.cursor.execute("SELECT {0} FROM group_meetings WHERE date=? "
                            " AND ({1} is null OR {1}='')".format(other, job),
                            (date_obj.isoformat(), ))
        other = self.cursor.fetchone()
        if other not in ['', None]:
            time_since_last[people_present.index(other[0])] = 0

        # turn timedelta into weight
        probs = [weight*random() for weight in time_since_last]
        # normalize
        probs = [prob/sum(probs) for prob in probs]

        # winner
        return people_present[probs.index(max(probs))]

    def add(self, date_str='', job='', person=''):
        if not self.is_valid_date(date_str):
            raise action.BadInputError('What is the date of the presentaton?'
                                       ' It must be one of "next" or "yyyy-mm-dd".')

        # get the data
        self.cursor.execute('SELECT * FROM group_meetings ORDER BY date')
        rows = self.cursor.fetchall()

        # find the date
        date_obj = None
        if date_str == 'next':
            last_date = datetime.strptime(rows[-1][1], '%Y-%m-%d').weekday()
            weekday_diff = datetime.today().weekday() - last_date
            date_obj = datetime.today().date() + timedelta(7) + weekday_diff
            # FIXME: message
        else:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        if job not in ['presenter', 'chair']:
            raise action.BadInputError('What job would you like me to assign?'
                                       ' It must be one of "presenter" or "chair".',
                                       args=(date_str,))

        if person == '':
            raise action.BadInputError('Who would you like to assign?'
                                       ' It should be a name or "random"',
                                       args=(date_str, job, ))

        if person == 'random':
            person = self.select_member_random(date_obj, job)
        self.cursor.execute('SELECT id FROM members WHERE id=?'
                            ' or name=? or userid=? or slack_id=?',
                            (person, )*4)
        matches = self.cursor.fetchall()
        if len(matches) == 0:
            raise action.BadInputError('I could not find anyone whose id, name,'
                                       ' userid, or slackid is {0}.\n'
                                       'Would you care to try again?'.format(person),
                                       args=(date_str, job,))
        elif len(matches) > 1:
            raise action.BadInputError('I found more than one person whose id, name,'
                                       ' userid, or slackid is {0}.\n'
                                       'Would you care to try again?'.format(person),
                                       args=(date_str, job,))
        else:
            person = matches[0][0]
        
        # Add data
        self.cursor.execute('SELECT * FROM group_meetings WHERE date=?',
                            date_obj.isoformat())
        rows = self.cursor.fetchall()
        print rows
        print len(rows)
        if len(rows) == 0:
            self.cursor.execute('INSERT INTO group_meetings (date, {0})'
                                ' VALUES (?,?)'.format(job),
                                (date_obj.isoformat(), person))
        elif len(rows) == 1:
            if rows[0][self.col_ids[job]] in [None, '']:
                self.cursor.execute('UPDATE group_meetings SET {0}=? WHERE id=?'.format(job),
                                    (person, rows[0][self.col_ids['id']]))
            else:
                # FIXME
                raise action.Messaging('There already is a person assigned.')
        else:
            # FIXME
            raise action.Messaging('There are more than one meetings to assign to.'
                                   " I don't know what to do.")
        self.db_conn.commit()

    def recount(self, *identifiers):
        """ Shows all presentations that satifies some conditions

        Parameters
        ----------
        identifiers : list
            Identifier of the presentations
            Each entry is string where ':' delimits the identifier from value
            e.g. ['presenter:name', 'chair:name']

        """
        for i in identifiers:
            if i.split(':')[0] not in ['presenter', 'chair', 'title', 'date']:
                raise action.BadInputError('All given options are the identifiers of a particular presentation.'
                                           ' Each identifier must be one of "presenter", "chair", "title", or "date".'
                                           ' The value of each identifier is delimited by "=".'
                                           ' For example, "presenter:person1 chair:person2"\n')
        where_command, vals, row = self._find_from_identifiers(*identifiers)
        if where_command == '' and row == 0:
            raise action.BadInputError('I could not find anyone using {0}'.format(identifiers))
        self.cursor.execute('SELECT * FROM group_meetings ORDER BY date DESC {0}'
                            ''.format(where_command))
        rows = self.cursor.fetchall()
        message = '{0:<4}{1:<10}{2:<20}{3:<20}{4:<40}\n'.format('id', 'date', 'presenter', 'chair', 'title')
        message += '\n'.join('{0:<4}{1:<10}{2:<20}{3:<20}{4:<40}'.format(*row) for row in rows)
        raise action.Messaging(message)
