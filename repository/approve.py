import pandas as pd
import psycopg2
import psycopg2.extras
import uuid


def approve_normal_data(db_connection):
    with db_connection as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """

                """
            )
