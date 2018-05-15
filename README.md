# MatterMost user reporting

Queries all users for a specific team from the Postgres DB of Mattermost. Assigns every user based on email address to a manager and then send the resulting userlist to the managers.

- Managers are defined in the separate managers.json file
- The email template is in message txt

By default the script looks for both files in the current running directory

## Install & use

1. `pip3 install psycopg2 sqlalchemy`
2. Modify message.txt to suit your needs
3. Fill out managers.json
4. Fix variables inside the script. Including:
    1. Team ID inside the SQL statement
    2. Mattermost config file location
    3. SMTP info
    4. Admin email, who's report includes all users that do not have a manager
5. `python3 mm-user-report.py`

NB! There is a commented out print statement near the end. You can comment that in and comment out the following send_message line to see all reports before sending.

## TODO

- Do not query from the DB, but use the API with a token.
- Variables as command line params.