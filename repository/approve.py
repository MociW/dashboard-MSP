import pandas as pd
import psycopg2
import psycopg2.extras
import uuid
from datetime import datetime


def approve_in_house_data(df, db_connection, year):
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

                    status = "APPROVE"

                    cursor.execute(
                        """
                        SELECT "id","jsp","msp","local_oh","tooling_oh","raw_material","labor","foh_fixed","foh_var",
                            "unfinish_depre","total_process_cost", "exclusive_investment", "total_cost" FROM "in_house_detail" 
                        WHERE "in_house_item" = %s AND "year_item" = %s
                        """,
                        (inserted_uuid, year),
                    )
                    detail_result = cursor.fetchone()

                    current_date = datetime.now()
                    formatted_date = current_date.strftime("%d-%m-%Y").upper()
                    response = f"Approve at {formatted_date}"
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
                                detail_result[1],
                                detail_result[2],
                                detail_result[3],
                                detail_result[4],
                                detail_result[5],
                                detail_result[6],
                                detail_result[7],
                                detail_result[8],
                                detail_result[9],
                                detail_result[10],
                                detail_result[11],
                                detail_result[12],
                                status,
                                detail_id,
                            ),
                        )

                        cursor.execute(
                            """
                            INSERT INTO "in_house_explanations" ("in_house_detail_id", "explanation", "explained_at")
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            """,
                            (
                                detail_id,
                                response,
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


def approve_out_house_data(df, db_connection, year):
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

                    status = "APPROVE"

                    # Check if we have an existing detail record for this part and year
                    cursor.execute(
                        """
                        SELECT "id", "price" FROM "out_house_detail" 
                        WHERE "out_house_item" = %s AND "year_item" = %s
                        """,
                        (inserted_uuid, year),
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
                                round(detail_result[1], 0),
                                status,
                                detail_id,
                            ),
                        )

                    current_date = datetime.now()
                    formatted_date = current_date.strftime("%d-%m-%Y").upper()
                    response = f"Approve at {formatted_date}"
                    cursor.execute(
                        """
                        INSERT INTO "out_house_explanations" ("out_house_detail_id", "explanation", "explained_at")
                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                        """,
                        (
                            detail_id,
                            response,
                        ),
                    )

                    # Commit the transaction
                    connection.commit()
                    success_count += 1

                except Exception as e:
                    error_message = f"Error updating row {index + 1} for part {row.get('part_no', 'unknown')} in out house: {e}"
                    failed_parts.append({"part_no": row.get("part_no", "unknown"), "row": index + 1, "error": str(e)})
                    connection.rollback()

    # Return summary statistics and failed parts
    return {"total": len(df), "success": success_count, "failed": len(failed_parts), "failed_parts": failed_parts}


def approve_packing_data(df, db_connection, year):
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
                            INSERT INTO "packing" ("id", "part_no", "part_name")
                            VALUES (%s, %s, %s) 
                            """,
                            (inserted_uuid, row["part_no"], row["part_name"]),
                        )
                    else:
                        # Part exists, update part_name if needed and use existing UUID
                        inserted_uuid = result[0]

                    status = "APPROVE"

                    # Check if we have an existing detail record for this part and year
                    cursor.execute(
                        """
                        SELECT "id","labor_cost","material_cost","inland_cost" FROM "packing_detail" 
                        WHERE "packing_item" = %s AND "year_item" = %s
                        """,
                        (inserted_uuid, year),
                    )

                    detail_result = cursor.fetchall()

                    detail_arr = []
                    for detail in detail_result:
                        detail_arr.append(detail)

                    if detail_arr:
                        # Update existing detail record
                        for detail in detail_arr:
                            cursor.execute(
                                """
                                UPDATE 
                                    "packing_detail"
                                SET 
                                    "labor_cost" = %s, 
                                    "material_cost" = %s, 
                                    "inland_cost" = %s, 
                                    "status" = %s
                                WHERE "id" = %s
                                """,
                                (
                                    round(detail[1], 0),
                                    round(detail[2], 0),
                                    round(detail[3], 0),
                                    status,
                                    detail[0],
                                ),
                            )

                    # Add new explanation
                    current_date = datetime.now()
                    formatted_date = current_date.strftime("%d-%m-%Y").upper()
                    response = f"Approve at {formatted_date}"
                    for detail_id in detail_arr:
                        cursor.execute(
                            """
                            INSERT INTO "packing_explanations" ("packing_detail_id", "explanation", "explained_at")
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            """,
                            (
                                detail_id[0],
                                response,
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
