'''
Query MatterMost instance DB for users of specific team and send notification email per domain.
User reporting to team reps on who from their team is present on the chat.

Requires psycopg2 and sqlalchemy
'''

import json
import smtplib
import warnings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template

import sqlalchemy


def query_db():
    '''
    Get the user info from MatterMost DB
    '''
    members = {}
    mmconf = '/opt/mattermost/config/config.json'
    url = json.load(open(mmconf))['SqlSettings']['DataSource']
    conn = sqlalchemy.create_engine(url, client_encoding='utf-8')
    # Suppress some unsupported partial index warnings for MetaData
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sqlalchemy.exc.SAWarning)
        meta = sqlalchemy.MetaData(bind=conn, reflect=True)

    users = meta.tables['users']
    tmb = meta.tables['teammembers']
    select = sqlalchemy.select([users.c.email,
                                users.c.nickname,
                                users.c.firstname,
                                users.c.lastname]) \
                                .where(users.c.id == tmb.c.userid) \
                                .where(tmb.c.teamid == 'TeamIDGoesHere') \
                                .where(users.c.deleteat == 0) \
                                .where(tmb.c.deleteat == 0)
    results = conn.execute(select).fetchall()

    for row in results:
        members[row[0]] = {'domain': row[0].split('@')[1],
                           'nickname': row[1],
                           'firstname': row[2],
                           'lastname': row[3],
                          }
    return members

def read_template(filename):
    '''
    Get email template file
    '''
    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)


def main():
    '''
    Send email to team reps about their users.
    '''
    reporting = {}
    managers = json.load(open('managers.json'))
    smtp = smtplib.SMTP(host='mx.example.com', port=25)
    smtp.connect()
    message_template = read_template('message.txt')
    members = query_db()

    # Build lists of managers and their users
    for email, values in managers.items():
        try:
            reporting[email].update({'name': values['name']})
        except KeyError:
            reporting[email] = {'name': values['name']}

        for member, properties in members.items():
            if properties['domain'] in values['domain']:
                try:
                    reporting[email]['users'].update({member: properties['nickname']})
                except KeyError:
                    reporting[email]['users'] = {member: properties['nickname']}

    # All users who did not get a manager are added to MM system admin list
    for member, properties in members.items():
        if member not in [x for v in reporting.values() for x in v['users']]:
            reporting['haam3r@example.com']['users'].update({member: 'Not reported'})

    # Send each team rep an email with their users
    for manager, values in reporting.items():
        msg = MIMEMultipart()
        users = ""

        for email, nick in values['users'].items():
            if not nick:
                users += '{0} - NO NICK\n'.format(email)
            else:
                users += '{0} - {1}\n'.format(email, nick)

        domain = ' '.join(managers.get(manager)['domain'])
        message = message_template.substitute(MANAGER_NAME=values['name'],
                                              USERS=users,
                                              DOMAIN=domain)
        msg['From'] = 'mattermostm@example.com'
        msg['To'] = manager
        msg['Subject'] = 'EXAMPLE ORG MatterMost user reporting'
        msg.attach(MIMEText(message, 'plain'))
        #print(msg)
        smtp.send_message(msg)
        del msg

    smtp.quit()

if __name__ == '__main__':
    main()
