
from src.smtp.db.config import connPool
import mysql

def Insert(
    sender, receiver:list, data
    ):
    
        # Inserting many rows as per receiver list length.
        insertQuery = "INSERT INTO setu_outbox(sender, receiver, data) VALUES (%s, %s, %s) "
        argSequence = [(sender, recv, data) for recv in receiver]

        try:
            result = connPool.executemany(sql=insertQuery, seq_args=argSequence, commit=True)
            if result is None:
                return True
        except mysql.connector.PoolError :
            return False
    