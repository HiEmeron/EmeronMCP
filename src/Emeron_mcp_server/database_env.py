from .utils.db_source import HITLSQLDatabase

class DataBaseEnv:
    def __init__(self, database: HITLSQLDatabase):
        self.database = database
        self.dialect = database.dialect
        self.mschema = database.mschema
        self.db_name = database.db_name
        self.mschema_str = self.mschema.to_mschema()