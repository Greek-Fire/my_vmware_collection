from ansible.errors import AnsibleError, AnsibleFileNotFound
from ansible.plugins.lookup import LookupBase
import sqlite3
import os

DOCUMENTATION = '''
---
module: sqlite_select_all
version_added: 1.0.0
short_description: show all content from table
description:
  - "SELECT * FROM TABLE." You can chagne the table name using the table option.
author:
  - "Louis Tiches"
options:
  path:
    description: The Path to the sqlite db
    required: true
    type: str
  table:
    description: The table we need to parse
    required: true
    type: str
'''

EXAMPLES = '''
- name: Get data from SQLite table
  debug:
    msg: "{{ lookup('sqlite', 'path=/path/to/database.db', table='mytable') }}"
'''

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        sql = []
        table = kwargs.get('table', 'mytable')
        path =  kwargs.get('path', '/path/to/database.db')

        if not os.path.isfile(str(path)):
            raise AnsibleFileNotFound(f'SQLite database file {path} does not exist')

        # Connect to the SQLite database
        conn = sqlite3.connect(path)
        c = conn.cursor()

        # Check if the table exists in the database
        c.execute(f"SELECT * FROM {table}")
        table_exists = c.fetchone()
        if table_exists is None:
            raise AnsibleError(f'Table {table} does not exist in the SQLite database {path}')

        # Execute the query
        c.execute(f"SELECT * FROM {table}")
        rows = c.fetchall()

        # Get the column names
        column_names = [i[0] for i in c.description]

        # Close the connection
        conn.close()

        # Append the rows as dictionary with headers as keys
        for row in rows:
          sql.append(dict(zip(column_names, row)))

        return sql
