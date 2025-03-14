import pandas as pd
import psycopg2
import psycopg2.extras
import uuid

psycopg2.extras.register_uuid()


def input_packing_new_data(excel_file, db_connection):
    df = pd.read_excel(excel_file)

    with db_connection as connection:
        with connection.cursor() as cursor:
            for index, row in df.iterrows():
                try:
                    # Check if part_no already exists
                    part_no = str(row["part_no"])
                    cursor.execute(
                        """
                        SELECT "id" FROM "packing" WHERE "part_no" = %s
                        """,
                        (part_no,),
                    )
                    result = cursor.fetchone()

                    if result:
                        inserted_uuid = result[0]
                    else:
                        inserted_uuid = uuid.uuid4()
                        cursor.execute(
                            """
                            INSERT INTO "packing" ("id", "part_no", "part_name")
                            VALUES (%s, %s, %s)
                            """,
                            (inserted_uuid, part_no, row["part_name"]),
                        )

                    cursor.execute(
                        """
                        INSERT INTO "packing_detail" ("packing_item", "destination", "model", 
                        "labor_cost", "material_cost", "inland_cost", "year_item", "created_at")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        """,
                        (
                            inserted_uuid,
                            row["destination"],
                            row["model"],
                            round(row["labor_cost"], 0),
                            round(row["material_cost"], 0),
                            round(row["inland_cost"], 0),
                            row["year"],
                        ),
                    )
                    # Remove the connection.commit() here - let context manager handle it

                except Exception as e:
                    print(f"Error inserting row {index + 1}: {e}")
                    # Remove the connection.rollback() here - let context manager handle it
                    # Just re-raise to trigger the rollback in __exit__
                    raise


def update_packing_data():
    print()
