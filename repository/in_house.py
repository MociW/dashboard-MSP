import pandas as pd
import psycopg2
import psycopg2.extras
import uuid

psycopg2.extras.register_uuid()


def input_in_house_new_data(excel_file, db_connection):
    # Read the Excel file
    df = pd.read_excel(excel_file)
    # Connect to PostgreSQL
    with db_connection as connection:
        with connection.cursor() as cursor:
            for index, row in df.iterrows():
                try:
                    # Check if part_no already exists
                    cursor.execute(
                        """
                        SELECT "id" FROM "in_house" WHERE "part_no" = %s
                        """,
                        (row["part_no"],),
                    )
                    result = cursor.fetchone()

                    if result:
                        # If part_no exists, use the existing UUID
                        inserted_uuid = result[0]
                    else:
                        # Generate a new UUID for the in_house table
                        inserted_uuid = uuid.uuid4()

                        # Insert into in_house
                        cursor.execute(
                            """
                            INSERT INTO "in_house" ("id", "part_no", "part_name")
                            VALUES (%s, %s, %s) 
                            """,
                            (inserted_uuid, row["part_no"], row["part_name"]),
                        )

                    # Insert into in_house_detail
                    cursor.execute(
                        """
                        INSERT INTO "in_house_detail" ("in_house_item", "jsp", "msp", "local_oh", "tooling_oh",
                        "raw_material", "labor", "foh_fixed", "foh_var", "unfinish_depre", "total_process_cost",
                        "exclusive_investment", "total_cost", "year_item", "created_at")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, CURRENT_TIMESTAMP)
                        """,
                        (
                            inserted_uuid,
                            round(row["jsp"], 0),
                            round(row["msp"], 0),
                            round(row["local_oh"], 0),
                            round(row["tooling_oh"], 0),
                            round(row["raw_material"], 0),
                            round(row["labor"], 0),
                            round(row["foh_fixed"], 0),
                            round(row["foh_var"], 0),
                            round(row["unfinish_depre"], 0),
                            round(row["total_process_cost"], 0),
                            round(row["exclusive_investment"], 0),
                            round(row["total_cost"], 0),
                            row["year"],
                        ),
                    )
                    db_connection.connection.commit()

                except Exception as e:
                    print(f"Error inserting row {index + 1}: {e}")
                    db_connection.connection.rollback()


def update_in_house_data():
    print()
