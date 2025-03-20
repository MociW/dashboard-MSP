import pandas as pd
import psycopg2
import psycopg2.extras
import uuid

psycopg2.extras.register_uuid()


def input_out_house_new_data(excel_file, db_connection):
    # Read the Excel file
    df = pd.read_excel(excel_file)
    df["part_no"] = df["part_no"].astype(str)

    failed_parts = []  # List to store failed part numbers
    success_count = 0  # Counter for successful updates

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
                    connection.connection.commit()
                    success_count += 1

                except Exception as e:
                    error_message = f"Error updating row {index + 1} for part {row.get('part_no', 'unknown')}: {e}"
                    print(error_message)
                    failed_parts.append({"part_no": row.get("part_no", "unknown"), "row": index + 1, "error": str(e)})
                    connection.rollback()

    return {"total": len(df), "success": success_count, "failed": len(failed_parts), "failed_parts": failed_parts}


def update_out_house_data(excel_file, db_connection):
    df = pd.read_excel(excel_file)
    df["part_no"] = df["part_no"].astype(str)

    failed_parts = []  # List to store failed part numbers
    success_count = 0  # Counter for successful updates

    with db_connection as connection:
        with connection.cursor() as cursor:
            for index, row in df.iterrows():
                try:
                    # Check if part_no exists
                    cursor.execute(
                        """
                        SELECT "id" FROM "out_house" WHERE "part_no" = %s
                        """,
                        (row["part_no"],),
                    )
                    result = cursor.fetchone()

                    if not result:
                        # If part doesn't exist, create it
                        inserted_uuid = uuid.uuid4()

                        cursor.execute(
                            """
                            INSERT INTO "out_house" ("id", "part_no", "part_name")
                            VALUES (%s, %s, %s) 
                            """,
                            (inserted_uuid, row["part_no"], row["part_name"]),
                        )
                    else:
                        # Part exists, update part_name if needed and use existing UUID
                        inserted_uuid = result[0]

                    # Format status (convert to uppercase and standardize)
                    status = row["status"].strip().upper()
                    if status == "A":
                        status = "APPROVE"
                    elif status == "D":
                        status = "PENDING"
                    else:
                        status = "PENDING"

                    # Check if we have an existing detail record for this part and year
                    cursor.execute(
                        """
                        SELECT "id" FROM "out_house_detail" 
                        WHERE "out_house_item" = %s AND "year_item" = %s
                        """,
                        (inserted_uuid, row["year"]),
                    )
                    detail_result = cursor.fetchone()

                    if detail_result:
                        # Update existing detail record
                        detail_id = detail_result[0]
                        cursor.execute(
                            """
                            UPDATE "out_house_detail"
                            SET "price" = %s, "status" = %s
                            WHERE "id" = %s
                            """,
                            (
                                round(row["price"], 0),
                                status,
                                detail_id,
                            ),
                        )

                    # Add new explanation
                    if row["reason"]:
                        cursor.execute(
                            """
                            INSERT INTO "out_house_explanations" ("out_house_detail_id", "explanation", "explained_at")
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            """,
                            (
                                detail_id,
                                row["reason"],
                            ),
                        )

                    # Commit the transaction
                    connection.commit()
                    success_count += 1

                except Exception as e:
                    error_message = f"Error updating row {index + 1} for part {row.get('part_no', 'unknown')}: {e}"
                    print(error_message)
                    failed_parts.append({"part_no": row.get("part_no", "unknown"), "row": index + 1, "error": str(e)})
                    connection.rollback()

    # Return summary statistics and failed parts
    return {"total": len(df), "success": success_count, "failed": len(failed_parts), "failed_parts": failed_parts}
