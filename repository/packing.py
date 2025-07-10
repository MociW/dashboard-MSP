import pandas as pd
import psycopg2
import psycopg2.extras
import uuid

psycopg2.extras.register_uuid()


def input_packing_new_data(excel_file, db_connection):
    df = pd.read_excel(excel_file)

    failed_parts = []  # List to store failed part numbers
    success_count = 0  # Counter for successful updates
    skipped_count = 0  # Counter for skipped entries

    with db_connection as connection:
        with connection.cursor() as cursor:
            for index, row in df.iterrows():
                try:
                    part_no = str(row["part_no"])
                    if len(part_no) > 10:
                        failed_parts.append(
                            {"part_no": part_no, "row": index + 1,
                             "error": "Part number exceeds maximum length (10 characters)"}
                        )
                        continue

                    # Check if part_no already exists
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

                    # Fix: Check for NaN values properly and convert before using in SQL
                    if pd.notna(row["model"]):
                        model_part = row["model"]
                    else:
                        model_part = ""

                    cursor.execute(
                        """
                        SELECT "id", "labor_cost", "material_cost", "inland_cost"
                        FROM "packing_detail"
                        WHERE "packing_item" = %s AND "year_item" = %s AND "destination" = %s AND "model" = %s
                        """,
                        (inserted_uuid, row["year"], row["destination"], model_part),
                    )

                    existing_entry = cursor.fetchone()

                    labor_cost = round(row["labor_cost"], 0)
                    material_cost = round(row["material_cost"], 0)
                    inland_cost = round(row["inland_cost"], 0)

                    if existing_entry:
                        # existing_entry = (id, labor_cost, material_cost, inland_cost)
                        # Update if any cost is less than new cost
                        if (existing_entry[1] < labor_cost or
                            existing_entry[2] < material_cost or
                            existing_entry[3] < inland_cost):
                            cursor.execute(
                                """
                                UPDATE "packing_detail"
                                SET "labor_cost" = %s,
                                    "material_cost" = %s,
                                    "inland_cost" = %s,
                                    "created_at" = CURRENT_TIMESTAMP
                                WHERE "id" = %s
                                """,
                                (labor_cost, material_cost, inland_cost, existing_entry[0])
                            )
                            success_count += 1
                        else:
                            skipped_count += 1
                            print(f'Skipping entry for part {part_no} with destination {row["destination"]} in year {row["year"]} - Already exists with equal or higher costs')
                            continue
                    else:
                        # Insert new packing_detail record
                        cursor.execute(
                            """
                            INSERT INTO "packing_detail" ("packing_item", "destination", "model", 
                            "labor_cost", "material_cost", "inland_cost", "year_item", "created_at")
                            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                            """,
                            (
                                inserted_uuid,
                                row["destination"],
                                model_part,
                                labor_cost,
                                material_cost,
                                inland_cost,
                                row["year"],
                            ),
                        )
                        success_count += 1

                except Exception as e:
                    error_message = f"Error processing row {index + 1} for part {row.get('part_no', 'unknown')}: {e}"
                    print(error_message)
                    failed_parts.append({"part_no": row.get("part_no", "unknown"), "row": index + 1, "error": str(e)})
                    connection.rollback()

    # Return details for further processing if needed
    return {"total": len(df), "success": success_count, "failed": len(failed_parts), "failed_parts": failed_parts}


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
                            INSERT INTO "packing" ("id", "part_no", "part_name")
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
                    detail_result = cursor.fetchall()

                    detail_id_arr=[]
                    for detail in detail_result:
                        detail_id_arr.append(detail[0])

                    if detail_id_arr:
                        # Update existing detail record
                        for detail_id in detail_id_arr:
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
                                    round(row["labor_cost"], 0),
                                    round(row["material_cost"], 0),
                                    round(row["inland_cost"], 0),
                                    status,
                                    detail_id,
                                ),
                            )

                    # Add new explanation
                    if row["reason"]:
                        for detail_id in detail_id_arr:
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
