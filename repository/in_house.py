import pandas as pd
import psycopg2
import psycopg2.extras
import uuid
psycopg2.extras.register_uuid()


def input_in_house_new_data(excel_file, db_connection):
    # Read the Excel file - ensure string conversion for part_no
    df = pd.read_excel(excel_file)

    # Explicitly convert part_no to string to avoid type errors
    df['part_no'] = df['part_no'].astype(str)

    failed_parts = []  # List to store failed part numbers
    success_count = 0  # Counter for successful updates
    skipped_count = 0  # Counter for skipped entries

    # Connect to PostgreSQL
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
                        SELECT "id" FROM "in_house" WHERE "part_no" = %s
                        """,
                        (part_no,),
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
                            (inserted_uuid, part_no, row["part_name"]),
                        )

                    # Check if the part number and year combination already exists
                    cursor.execute(
                        """
                        SELECT "id" FROM "in_house_detail" 
                        WHERE "in_house_item" = %s AND "year_item" = %s
                        """,
                        (inserted_uuid, row["year"]),
                    )

                    existing_entry = cursor.fetchone()

                    if existing_entry:
                        # Skip if the entry already exists
                        skipped_count += 1
                        print(f"Skipping entry for part {part_no} in year {row['year']} - Already exists")
                        continue

                    # Insert into in_house_detail with proper rounding
                    cursor.execute(
                        """
                        INSERT INTO "in_house_detail" ("in_house_item","lva","non_lva","tooling","process_cost","total_cost", "year_item", "created_at")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        """,
                        (
                            inserted_uuid,
                            # round(float(row["jsp"]), 0),
                            # round(float(row["msp"]), 0),
                            # round(float(row["local_oh"]), 0),
                            # round(float(row["tooling_oh"]), 0),
                            # round(float(row["raw_material"]), 0),
                            # round(float(row["labor"]), 0),
                            # round(float(row["foh_fixed"]), 0),
                            # round(float(row["foh_var"]), 0),
                            # round(float(row["unfinish_depre"]), 0),
                            # round(float(row["total_process_cost"]), 0),
                            # round(float(row["exclusive_investment"]), 0),
                            round(float(row["lva"]), 0),
                            round(float(row["non_lva"]), 0),
                            round(float(row["tooling"]), 0),
                            round(float(row["process_cost"]), 0),
                            round(float(row["lva"] + row["non_lva"] + row["tooling"] + row["process_cost"]), 0),
                            row["year"],
                        ),
                    )

                    connection.commit()
                    success_count += 1

                except Exception as e:
                    error_message = f"Error processing row {index + 1} for part {row.get('part_no', 'unknown')}: {e}"
                    print(error_message)
                    failed_parts.append({"part_no": row.get("part_no", "unknown"), "row": index + 1, "error": str(e)})
                    connection.rollback()

    # Print summary of operation
    print("Operation Summary:")
    print(f"Total rows processed: {len(df)}")
    print(f"Successful insertions: {success_count}")
    print(f"Skipped entries: {skipped_count}")
    print(f"Failed entries: {len(failed_parts)}")

    # Return details for further processing if needed
    return {"total": len(df), "success": success_count, "failed": len(failed_parts), "failed_parts": failed_parts}


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
                            INSERT INTO "in_house" ("id", "part_no", "part_name")
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
                                "lva" = %s,                               
                                "non_lva" = %s,                               
                                "tooling" = %s,                               
                                "process_cost" = %s,                               
                                "total_cost" = %s,
                                "status" = %s
                            WHERE
                                "id" = %s
                            """,
                            (
                                round(float(row["lva"]), 0),
                                round(float(row["non_lva"]), 0),
                                round(float(row["tooling"]), 0),
                                round(float(row["process_cost"]), 0),
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
