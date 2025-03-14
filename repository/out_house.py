import pandas as pd
import psycopg2
import psycopg2.extras
import uuid

psycopg2.extras.register_uuid()


def input_out_house_new_data(excel_file, db_connection):
    # Read the Excel file
    df = pd.read_excel(excel_file)
    df["part_no"] = df["part_no"].astype(str)

    # Use the provided connection
    with db_connection as connection:
        with connection.cursor() as cursor:
            # Iterate over rows and process each part
            for index, row in df.iterrows():
                try:
                    # Check if part_no already exists in out_house
                    cursor.execute(
                        """
                        SELECT "id" FROM "out_house" WHERE "part_no" = %s
                        """,
                        (row["part_no"],),
                    )
                    result = cursor.fetchone()
                    if result:
                        # Use existing UUID if part already exists
                        out_house_id = result[0]
                    else:
                        # Create new out_house entry
                        out_house_id = uuid.uuid4()
                        cursor.execute(
                            """
                            INSERT INTO "out_house" ("id", "part_no", "part_name")
                            VALUES (%s, %s, %s)
                            """,
                            (out_house_id, row["part_no"], row["part_name"]),
                        )

                    # Insert into out_house_detail
                    cursor.execute(
                        """
                        INSERT INTO "out_house_detail" ("out_house_item", "price", "source", "year_item", "created_at")
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        RETURNING "id"
                        """,
                        (
                            out_house_id,
                            round(row["price"], 0),
                            row["source"],
                            row["year"],
                        ),
                    )
                    db_connection.connection.commit()

                except Exception as e:
                    print(f"Error inserting row {index + 1}: {e}")
                    db_connection.connection.rollback()


def update_out_house_data(excel_file, db_connection):
    print()
