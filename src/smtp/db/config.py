import os
from dotenv import load_dotenv
from mysql.connector import pooling

load_dotenv()


DB_NAME= os.environ.get('DB_NAME')
DB_USER= os.environ.get('DB_USER')
DB_PASSWORD= os.environ.get('DB_PASSWORD')
DB_HOST= os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT= os.environ.get('DB_PORT', '3306')

db_config = {
    "host":DB_HOST,
    "port":DB_PORT,
    "user":DB_USER,
    "password":DB_PASSWORD,
    "database":DB_NAME,
}


class MySQLPool:
    def __init__(
        self,
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        pool_name='setu',
        pool_size= 30
    ):
        res = {}
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database = database

        res["host"] = self._host
        res["port"] = self._port
        res["user"] = self._user
        res["password"] = self._password
        res["database"] = self._database
        self.dbconfig = res
        self.pool = self._create_pool(pool_name=pool_name, pool_size=pool_size)

    def _create_pool(self, pool_name="setu", pool_size=3):
            """
            Create a connection pool, after created, the request of connecting
            MySQL could get a connection from this pool instead of request to
            create a connection.
            :param pool_name: the name of pool, default is "mypool"
            :param pool_size: the size of pool, default is 3
            :return: connection pool
            """
            pool = pooling.MySQLConnectionPool(
                pool_name=pool_name,
                pool_size=pool_size,
                pool_reset_session=True,
                **self.dbconfig
            )
            return pool

    def close(self, conn, cursor):
            """
            A method used to close connection of mysql.
            :param conn:
            :param cursor:
            :return:
            """
            cursor.close()
            conn.close()

    def execute(self, sql, args=None, commit=False):
            """
            Execute a sql, it could be with args and with out args. The usage is
            similar with execute() function in module pymysql.
            :param sql: sql clause
            :param args: args need by sql clause
            :param commit: whether to commit
            :return: if commit, return None, else, return result
            """
            # get connection form connection pool instead of create one.
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            if args:
                cursor.execute(sql, args)
            else:
                cursor.execute(sql)
            if commit is True:
                conn.commit()
                self.close(conn, cursor)
                return None
            else:
                res = cursor.fetchall()
                self.close(conn, cursor)
                return res
            
    def get_conn(self):
        conn = self.pool.get_connection()
        return conn


connPool = MySQLPool(**db_config)
