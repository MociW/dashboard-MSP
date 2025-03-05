import pandas as pd
import psycopg2
import psycopg2.extras
import uuid

# Register UUID type with psycopg2
psycopg2.extras.register_uuid()


def load_excel_to_postgres(df, conn):
    df["Part No"] = df["Part No"].astype(str)

    try:
        cursor = conn.cursor()

        for index, row in df.iterrows():
            try:
                part_no = row["Part No"]
                part_name = row["Part Name"]
                price = round(row["Price"], 0)
                source = row["Source"]
                year = row["Year"]
                explanation = row.get("Explanation", None)

                # Check if part_no exists in out_house
                cursor.execute(
                    """
                    SELECT id FROM out_house WHERE part_no = %s
                    """,
                    (part_no,),
                )
                out_house_result = cursor.fetchone()

                if out_house_result:
                    out_house_id = out_house_result[0]
                else:
                    # Insert new out_house record
                    out_house_id = uuid.uuid4()
                    cursor.execute(
                        """
                        INSERT INTO out_house (id, part_no, part_name)
                        VALUES (%s, %s, %s)
                        """,
                        (out_house_id, part_no, part_name),
                    )

                # Check if out_house_detail for same year + source exists
                cursor.execute(
                    """
                    SELECT id, price FROM out_house_detail
                    WHERE out_house_item = %s AND year_item = %s AND source = %s
                    """,
                    (out_house_id, year, source),
                )
                detail_result = cursor.fetchone()

                explanation_must_exist = False  # flag if we force explanation insert after update

                if detail_result:
                    out_house_detail_id, existing_price = detail_result

                    if existing_price != price:
                        # Update price if different
                        cursor.execute(
                            """
                            UPDATE out_house_detail
                            SET price = %s
                            WHERE id = %s
                            """,
                            (price, out_house_detail_id),
                        )
                        explanation_must_exist = True  # explanation required after price update
                    # No price update if it matches — explanation still allowed

                else:
                    # Insert new out_house_detail if no matching record
                    cursor.execute(
                        """
                        INSERT INTO out_house_detail (out_house_item, price, source, year_item, created_at)
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        RETURNING id
                        """,
                        (out_house_id, price, source, year),
                    )
                    out_house_detail_id = cursor.fetchone()[0]
                    explanation_must_exist = True  # explanation required for new detail

                # Explanation handling - always insert if present or if explanation must exist
                if explanation or explanation_must_exist:
                    if explanation is None:
                        explanation = "(Explanation required due to price update but missing in input)"

                    cursor.execute(
                        """
                        INSERT INTO out_house_explanations (out_house_detail_id, explanation, explained_at)
                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                        """,
                        (out_house_detail_id, explanation),
                    )

                conn.commit()

            except Exception as e:
                print(f"Error processing row {index + 1}: {e}")
                conn.rollback()

    except Exception as e:
        print(f"Database connection error: {e}")

    finally:
        cursor.close()
        conn.close()
