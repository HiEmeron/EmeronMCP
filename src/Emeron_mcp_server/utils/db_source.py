from typing import Any, Dict, List, Optional, Tuple

from llama_index.core import SQLDatabase
from sqlalchemy import MetaData, Table, select, text
from sqlalchemy.engine import Engine

from .db_mschema import MSchema
from .db_util import examples_to_str, preprocess_sql_query


class HITLSQLDatabase(SQLDatabase):
    def __init__(self, engine: Engine, schema: Optional[str] = None, metadata: Optional[MetaData] = None,
                 ignore_tables: Optional[List[str]] = None, include_tables: Optional[List[str]] = None,
                 sample_rows_in_table_info: int = 3, indexes_in_table_info: bool = False,
                 custom_table_info: Optional[dict] = None, view_support: bool = False, max_string_length: int = 300,
                 mschema: Optional[MSchema] = None, db_name: Optional[str] = ''):
        super().__init__(engine, schema, metadata, ignore_tables, include_tables, sample_rows_in_table_info,
                         indexes_in_table_info, custom_table_info, view_support, max_string_length)

        self._db_name = db_name
        self._usable_tables = [table_name for table_name in self._usable_tables if self._inspector.has_table(table_name, schema)]
        self._dialect = engine.dialect.name
        if mschema is not None:
            self._mschema = mschema
        else:
            self._mschema = MSchema(db_id=db_name, schema=schema)
            self.init_mschema()

    @property
    def mschema(self) -> MSchema:
        """Return M-Schema"""
        return self._mschema

    @property
    def db_name(self) -> str:
        """Return db_name"""
        return self._db_name

    def get_pk_constraint(self, table_name: str) -> Dict:
        return self._inspector.get_pk_constraint(table_name, self._schema)['constrained_columns']

    def get_table_comment(self, table_name: str):
        try:
            return self._inspector.get_table_comment(table_name, self._schema)['text']
        except:    
            return ''

    def default_schema_name(self) -> Optional[str]:
        return self._inspector.default_schema_name

    def get_schema_names(self) -> List[str]:
        return self._inspector.get_schema_names()

    def get_foreign_keys(self, table_name: str):
        return self._inspector.get_foreign_keys(table_name, self._schema)

    def get_unique_constraints(self, table_name: str):
        return self._inspector.get_unique_constraints(table_name, self._schema)
    
    def fectch_distinct_values(self, table_name: str, column_name: str, max_num: int = 5):
        table = Table(table_name, self.metadata_obj, autoload_with=self._engine)
    
        query = select(table.c[column_name]).distinct().limit(max_num)
        values = []
        with self._engine.connect() as connection:
            result = connection.execute(query)
            distinct_values = result.fetchall()
            for value in distinct_values:
                if value[0] is not None and value[0] != '':
                    values.append(value[0])
        return values
    
    def fetch(self, sql_query: str):
        sql_query = preprocess_sql_query(sql_query)

        with self._engine.begin() as connection:
            try:
                cursor = connection.execute(text(sql_query))
                records = cursor.fetchall()
                records = [tuple(row) for row in records]
                return True, records
            except Exception as e:
                # print("An exception occurred during SQL execution.\n", e)
                records = str(e)
            return False, records

    def fetch_with_column_name(self, sql_query: str):
        sql_query = preprocess_sql_query(sql_query)

        with self._engine.begin() as connection:
            try:
                cursor = connection.execute(text(sql_query))
                columns = cursor.keys()
                records = cursor.fetchall()
            except Exception as e:
                # print("An exception occurred during SQL execution.\n", e)
                records = None
                columns = []
            return records, columns

    def fetch_with_error_info(self, sql_query: str) -> Tuple[List, str]:
        info = ''
        sql_query = preprocess_sql_query(sql_query)
        with self._engine.begin() as connection:
            try:
                cursor = connection.execute(text(sql_query))
                records = cursor.fetchall()
            except Exception as e:
                info = str(e)
                records = None
        return records, info

    def fetch_truncated(self, sql_query: str, max_rows: Optional[int] = None, max_str_len: int = 30) -> Dict:
        sql_query = preprocess_sql_query(sql_query)
        with self._engine.begin() as connection:
            try:
                cursor = connection.execute(text(sql_query))
                result = cursor.fetchall()
                truncated_results = []
                if max_rows:
                    result = result[:max_rows]
                for row in result:
                    truncated_row = tuple(
                        self.truncate_word(column, length=max_str_len)
                        for column in row
                    )
                    truncated_results.append(truncated_row)
                return {"truncated_results": truncated_results, "fields": list(cursor.keys())}
            except Exception as e:
                # print("An exception occurred during SQL execution.\n", e)
                # records = None
                records = str(e)
                return {"truncated_results": records, "fields": []}

    def trunc_result_to_markdown(self, sql_res: Dict) -> str:
        """

        """
        truncated_results = sql_res.get("truncated_results", [])
        fields = sql_res.get("fields", [])

        if not isinstance(truncated_results, list):
            return str(truncated_results)

        header = "| " + " | ".join(fields) + " |"
        separator = "| " + " | ".join(["---"] * len(fields)) + " |"
        rows = []
        for row in truncated_results:
            rows.append("| " + " | ".join(str(value) for value in row) + " |")
        markdown_table = "\n".join([header, separator] + rows)
        return markdown_table
    

    def execute(self, sql_query: str, timeout=5) -> Any:
        # import concurrent.futures
        sql_query = preprocess_sql_query(sql_query)

        with self._engine.begin() as connection:
            try:
                cursor = connection.execute(text(sql_query))
                return True
            except Exception as e:
                info = str(e)
                print("SQL执行异常：", info)
                return None

    def init_mschema(self):
        for table_name in self._usable_tables:
            table_comment = self.get_table_comment(table_name)
            table_comment = '' if table_comment is None else table_comment.strip()
            self._mschema.add_table(table_name, fields={}, comment=table_comment)
            pks = self.get_pk_constraint(table_name)

            fks = self.get_foreign_keys(table_name)
            for fk in fks:
                referred_schema = fk['referred_schema']
                for c, r in zip(fk['constrained_columns'], fk['referred_columns']):
                    self._mschema.add_foreign_key(table_name, c, referred_schema, fk['referred_table'], r)

            fields = self._inspector.get_columns(table_name, schema=self._schema)
            for field in fields:
                field_type = f"{field['type']!s}"
                field_name = field['name']
                if field_name in pks:
                    primary_key = True
                else:
                    primary_key = False

                field_comment = field.get("comment", None)
                field_comment = "" if field_comment is None else field_comment.strip()
                autoincrement = field.get('autoincrement', False)
                default = field.get('default', None)
                if default is not None:
                    default = f'{default}'

                try:
                    examples = self.fectch_distinct_values(table_name, field_name, 5)
                except:
                    examples = []
                examples = examples_to_str(examples)

                self._mschema.add_field(table_name, field_name, field_type=field_type, primary_key=primary_key,
                    nullable=field['nullable'], default=default, autoincrement=autoincrement,
                    comment=field_comment, examples=examples)

    def sync_to_local(self, local_engine: Engine):

        from sqlalchemy.orm import sessionmaker

        local_metadata = MetaData()

        # # 连接到远程数据库
        remote_metadata = MetaData()
        remote_metadata.reflect(bind=self._engine)

        remote_metadata.create_all(bind=self._engine)

        print(remote_metadata.tables.keys())
        # 同步表结构和数据
        for table_name in remote_metadata.tables:
            remote_table = Table(table_name, remote_metadata, autoload_with=self._engine)
            print(f"Syncing table {table_name}...")

            # 创建本地表
            remote_table.metadata = local_metadata
            local_metadata.drop_all(local_engine)
            local_metadata.create_all(local_engine, tables=[remote_table])

            # 将数据同步到本地
            Session = sessionmaker(bind=self._engine)
            session = Session()
            with local_engine.begin() as local_connection:
                data = session.query(remote_table).all()
                columns = remote_table.columns.keys()
                insert_data = [dict(zip(columns, d)) for d in data]
                local_connection.execute(remote_table.insert(), insert_data)

        print("Sync complete.")


