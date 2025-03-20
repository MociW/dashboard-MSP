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


def update_packing_data(excel_file, db_connection):
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
                        SELECT "id" FROM "packing" WHERE "part_no" = %s
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
                        SELECT "id" FROM "packing_detail" 
                        WHERE "packing_item" = %s AND "year_item" = %s
                        """,
                        (inserted_uuid, row["year"]),
                    )
                    detail_result = cursor.fetchone()

                    if detail_result:
                        # Update existing detail record
                        detail_id = detail_result[0]
                        cursor.execute(
                            """
                            UPDATE "packing_detail"
                            SET "price" = %s, "status" = %s
                            WHERE "id" = %s
                            """,
                            (
                                round(row["labor_cost"], 0),
                                round(row["material_cost"], 0),
                                round(row["inland_cost"], 0),
                                status,
                                detail_id,
                            ),
                        )

                    # Add new explanation
                    if row["reason"]:
                        cursor.execute(
                            """
                            INSERT INTO "packing_explanations" ("packing_detail_id", "explanation", "explained_at")
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
