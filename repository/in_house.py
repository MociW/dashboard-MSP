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


def update_in_house_data(excel_file, db_connection):
    df = pd.read_excel(excel_file)
    df["part_no"] = df["part_no"].astype(str)

    failed_parts = []  # List to store failed part numbers
    success_count = 0  # Counter for successful updates

    with db_connection as connection:
        with connection.cursor() as cursor:
            for index, row in df.iterrows():
                try:
                    cursor.execute(
                        """
                            SELECT "id" FROM "in_house" WHERE "part_no" = %s
                            """,
                        (row["part_no"],),
                    )
                    result = cursor.fetchone()

                    if not result:
                        inserted_uuid = uuid.uuid4()

                        cursor.execute(
                            """
                            INSERT INTO "out_house" ("id", "part_no", "part_name")
                            VALUES (%s, %s, %s) 
                            """,
                            (inserted_uuid, row["part_no"], row["part_name"]),
                        )
                    else:
                        inserted_uuid = result[0]

                    status = row["status"].strip().upper()
                    if status == "A":
                        status = "APPROVE"
                    elif status == "D":
                        status = "PENDING"
                    else:
                        status = "PENDING"

                    cursor.execute(
                        """
                        SELECT "id" FROM "in_house_detail" 
                        WHERE "in_house_item" = %s AND "year_item" = %s
                        """,
                        (inserted_uuid, row["year"]),
                    )
                    detail_result = cursor.fetchone()

                    if detail_result:
                        detail_id = detail_result[0]
                        cursor.execute(
                            """
                            UPDATE
                                "in_house_detail"
                            SET
                                "jsp" = %s,
                                "msp" = %s,
                                "local_oh" = %s,
                                "tooling_oh" = %s,
                                "raw_material" = %s,
                                "labor" = %s,
                                "foh_fixed" = %s,
                                "foh_var" = %s,
                                "unfinish_depre"= %s,
                                "total_process_cost" = %s,
                                "exclusive_investment"= %s,
                                "total_cost" = %s,
                                "status" = %s
                            WHERE
                                "id" = %s
                            """,
                            (
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
                                status,
                                detail_id,
                            ),
                        )

                    if row["reason"]:
                        cursor.execute(
                            """
                            INSERT INTO "in_house_explanations" ("in_house_detail_id", "explanation", "explained_at")
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            """,
                            (
                                detail_id,
                                row["reason"],
                            ),
                        )

                    connection.commit()
                    success_count += 1

                except Exception as e:
                    error_message = f"Error updating row {index + 1} for part {row.get('part_no', 'unknown')}: {e}"
                    print(error_message)
                    failed_parts.append({"part_no": row.get("part_no", "unknown"), "row": index + 1, "error": str(e)})
                    connection.rollback()

    return {"total": len(df), "success": success_count, "failed": len(failed_parts), "failed_parts": failed_parts}
