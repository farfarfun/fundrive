import logging
import os
import sqlite3
from datetime import datetime
from typing import List

import pandas as pd
from funbuild.shell import run_shell


class BaseTable:
    """
    表维度的底层数据库的通用实现
    """

    def __init__(self, table_name: str = "default_table", columns: List[str] = None):
        """
        初始化一个通用数据库
        :param table_name: 表名
        :param columns: 字段列表
        """
        self.table_name = table_name
        self.columns = columns
        self.logger = logging.getLogger(table_name)
        self.conn = None
        self.cursor = None

    def execute(self, sql, commit=True, *args, **kwargs):
        """
        sql执行核心
        :param commit: 是否需要commit
        :param sql: 执行sql
        :return: 执行结果
        """
        try:
            rows = self.cursor.execute(sql)
            if commit:
                self.conn.commit()
            return rows
        except Exception as e:
            print(f"{sql}  with error:{e}")
            return

    def close(self):
        """
        关闭数据库连接
        """
        self.cursor.close()
        self.conn.close()

    def select_pd(self, sql="select * from table_name"):
        """
        将表数据转成pandas的DataFrame
        :param sql: sql
        :return: DataFrame
        """
        sql = self.sql_format(sql)
        return pd.read_sql(sql, self.conn)

    def insert(self, properties: dict):
        """
        插入单条记录，当表设置唯一键插入时，如果唯一键已存在，则返回
        :param properties: 记录以字典形式保存，key是字段名，value是字段值
        :return: 插入 成功or失败
        """
        properties = self.encode(properties)
        keys, values = self._properties2kv(properties)

        sql = """insert or ignore into {table_name} ({columns}) values ({value})""".format(
            table_name=self.table_name, columns=", ".join(keys), value=", ".join(values)
        )
        return self.execute(sql)

    def insert_list(self, property_list: List[dict]):
        """
        批量插入
        :param property_list:
        :return:
        """
        values = [
            tuple([properties.get(key, "") for key in self.columns])
            for properties in property_list
        ]
        sql = "insert or ignore into {} values ({})".format(
            self.table_name, ",".join(["?"] * len(self.columns))
        )

        self.cursor.executemany(sql, values)
        self.conn.commit()
        return True

    def update(self, properties: dict, condition: dict):
        """
        更新数据
        :param properties: 需要更新的字段
        :param condition:  where条件
        :return: 更新 成功or失败
        """
        properties = self.encode(properties)
        equal = self._condition2equal(properties)
        equal2 = self._condition2equal(condition)
        sql = """update  {} set {} where {}""".format(
            self.table_name, ", ".join(equal), " and ".join(equal2)
        )
        return self.execute(sql)

    def update_or_insert(self, properties: dict, condition: dict = None):
        """
        更新或者插入，首先尝试更新，更新失败则插入
        :param properties: 需要更新的字段
        :param condition:  where条件
        :return: 更新/插入 成功or失败
        """
        up = self.update(properties, condition)
        if up is None or up.rowcount == 0:
            return self.insert(properties)
        else:
            return up

    def decode(self, properties: dict):
        """
        需要子类实现
        有些数据插入时可能需要编码/加密等特殊操作，同时，取数据后需要有对应的解码/解密操作，默认不编码/加密
        :param properties: 记录数据
        :return: 编码/加密后的数据
        """
        return properties

    def encode(self, properties: dict):
        """
        需要子类实现
        有些数据插入时可能需要编码/加密等特殊操作，同时，取数据后需要有对应的解码/解密操作，默认不解码/解密
        :param properties: 编码/加密后记录数据
        :return: 解码/加密后的数据
        """
        return properties

    def count(self, properties: dict):
        """
        满足条件的数据量
        :param properties: 记录数
        :return: 记录条数
        """
        properties = properties or {}
        values = []
        for key in self.columns:
            value = str(properties.get(key, ""))
            if len(value) > 0 and len(key) > 0:
                values.append("{}='{}'".format(key, value.replace("'", "")))

        sql = """select count(1) from {} where {}""".format(
            self.table_name, " and ".join(values)
        )

        rows = self.execute(sql)
        for row in rows:
            return row[0]
        return 0

    def select_all(self):
        """
        返回全表数据
        """
        return self.select("select * from table_name")

    def select(self, sql=None, condition: dict = None):
        """
        根据sql或者指定条件选择数据
        :param sql: sql
        :param condition: 条件
        :return: 记录list
        """
        if sql is None:
            equal2 = self._condition2equal(condition)
            sql = """select * from {} where {}""".format(
                self.table_name, " and ".join(equal2)
            )
        else:
            sql = self.sql_format(sql)

        rows = self.execute(sql)
        return [] if rows is None else [dict(zip(self.columns, row)) for row in rows]

    def _properties2kv(self, properties: dict):
        """
        将输入的记录数据转换成表的字段名和字段值数据
        :param properties: 记录数据
        :return: keys and values
        """
        if self.columns is None:
            raise Exception("origin_keys cannot be None")
        keys = []
        values = []
        for key in self.columns:
            value = str(properties.get(key, "")).replace("'", "")
            if len(key) > 0 and len(value) > 0:
                keys.append(key)
                values.append("'{}'".format(value))
        return keys, values

    def _condition2equal(self, properties: dict):
        """
        将输入的记录数据转换成表的字段名和字段值数据的等式
        :param properties: 记录数据
        :return: 等式
        """
        if isinstance(properties, str):
            return properties
        if self.columns is None:
            raise Exception("origin_keys cannot be None")
        equals = []
        for key in self.columns:
            value = properties.get(key, None)

            if len(key) > 0 and value is not None:
                if isinstance(value, str):
                    value = value.replace("'", "")
                    equals.append("{}='{}'".format(key, value))
                else:
                    equals.append("{}={}".format(key, value))
        return equals

    def sql_format(self, sql):
        """
        对sql进行格式化，如一些特定字符串的替换
        :param sql: sql
        :return: 格式化之后的sql
        """
        sql = sql.replace("table_name", self.table_name)
        return sql

    def delete(self, condition=None):
        """
        删除表
        :param condition:
        :return:
        """
        if condition is None:
            sql = "delete from {}".format(self.table_name)
        elif isinstance(condition, str):
            sql = "delete from {} where {}".format(self.table_name, condition)
        elif isinstance(condition, dict):
            sql = "delete from {} where {}".format(
                self.table_name, self._condition2equal(condition)
            )
        else:
            sql = None
        if sql is not None:
            self.execute(sql)
            self.logger.info("delete records with sql = {}".format(sql))

    def add_columns(self, col_name, col_format: str = "VARCHAR(10)"):
        sql = f"ALTER TABLE table_name ADD COLUMN {col_name} {col_format} "
        sql = self.sql_format(sql)
        return self.execute(sql=sql)


class SqliteTable(BaseTable):
    def __init__(self, db_path, conn=None, lanzou_fid=None, *args, **kwargs):
        super(SqliteTable, self).__init__(*args, **kwargs)
        self.db_path = db_path
        self.logger.info("db path:{}".format(self.db_path))

        self.lanzou_fid = lanzou_fid
        if not os.path.exists(os.path.dirname(self.db_path)):
            os.makedirs(os.path.dirname(self.db_path))
        if lanzou_fid is not None and not os.path.exists(self.db_path):
            self.logger.info("file not exist,load from lanzou.")
            self.db_load()
        self.conn = conn or sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def save_and_truncate(self):
        result = pd.read_sql("select * from {}".format(self.table_name), self.conn)

        count = len(result)
        path = "{}/{}-{}-{}".format(
            os.path.dirname(self.db_path),
            self.table_name,
            count,
            datetime.now().strftime("%Y%m%d#%H:%M:%S"),
        )
        result.to_csv(path)
        self.logger.info("save to csv:{}->{}".format(count, path))

        self.execute("delete from {}".format(self.table_name))
        self.logger.info("delete from {}".format(self.table_name))
        self.vacuum()
        return result

    def to_csv(self, condition, path=None, pop=False, *args, **kwargs):
        if condition is None:
            sql = "select * from {}".format(self.table_name)
        else:
            sql = "select * from {} where {}".format(self.table_name, condition)

        path = path or (
            "{}/{}-{}".format(
                os.path.dirname(self.db_path),
                self.table_name,
                datetime.now().strftime("%Y%m%d#%H:%M:%S"),
            )
        )
        self.logger.info("save to csv -> {}".format(path))

        cmd = 'sqlite3 -header -csv {db_path} "{sql};" > {path}'.format(
            db_path=self.db_path, path=path, sql=sql
        )
        run_shell(cmd)
        if pop:
            self.delete(condition)
            self.vacuum()
        return path

    def pop_to_csv(self, condition, path=None):
        return self.to_csv(condition, path=path, pop=True)

    def vacuum(self):
        """
        数据库清理
        """
        self.execute("VACUUM")
        self.logger.info("数据库VACUUM")

    def insert_list(self, property_list: List[dict]):
        """
        批量插入
        :param property_list:
        :return:
        """
        values = [
            tuple([properties.get(key, "") for key in self.columns])
            for properties in property_list
        ]
        sql = "insert or ignore into {} values ({})".format(
            self.table_name, ",".join(["?"] * len(self.columns))
        )

        self.cursor.executemany(sql, values)
        self.conn.commit()
        return True

    def db_load(self):
        from fundrive.lanzou import LanZouCloud

        downer = LanZouCloud()
        downer.ignore_limits()
        downer.login_by_cookie()
        files = downer.get_file_list(folder_id=self.lanzou_fid)
        if len(files) > 0:
            files = sorted(files, key=lambda x: x["id"])
            downer.down_file_by_id(
                files[-1]["id"],
                save_path=os.path.dirname(self.db_path),
                file_name=os.path.basename(self.db_path),
            )

    def db_save(self):
        from fundrive.lanzou import LanZouCloud

        downer = LanZouCloud()
        downer.ignore_limits()
        downer.login_by_cookie()
        # file_name = f'{datetime.now().strftime("%Y%m%d%H%M%S")}-{os.path.basename(self.db_path)}'
        file_name = f'db-{datetime.now().strftime("%Y%m%d%H%M%S")}-{os.path.basename(self.db_path)}'
        return downer.upload_file(
            file_path=self.db_path, folder_id=self.lanzou_fid, file_name=file_name
        )


class MysqlTable(BaseTable):
    def __init__(
        self,
        cursor=None,
        host=None,
        user=None,
        password=None,
        database=None,
        *args,
        **kwargs,
    ):
        super(MysqlTable, self).__init__(*args, **kwargs)
        import pymysql

        self.conn = cursor or pymysql.connect(
            host=host, user=user, password=password, database=database
        )
        self.cursor = self.conn.cursor()
