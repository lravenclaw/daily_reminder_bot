class DatabaseRegisterError(Exception):
    default_detail = 'User already exist.'

class DatabaseSelectError(Exception):
    default_detail = 'No such user found.'

class SQLiteError(Exception):
    default_detail = 'Can\'t read from database file.'