import pandas as pd
import psycopg2
import psycopg2.extras
import uuid

# Register UUID type with psycopg2
psycopg2.extras.register_uuid()


def status_product_two_year_out_house(years):
    query_status = """
    WITH dataframe AS (
        SELECT DISTINCT i.part_no, ih.year_item
        FROM out_house i
        JOIN out_house_detail ih ON i.id = ih.out_house_item
        WHERE ih.year_item IN ({years})
    )
    SELECT
        part_no AS "Part No",
        CASE
            WHEN MAX(CASE WHEN year_item = {year1} THEN 1 ELSE 0 END) = 1 AND
                 MAX(CASE WHEN year_item = {year2} THEN 1 ELSE 0 END) = 1 THEN 'Remain'
            WHEN MAX(CASE WHEN year_item = {year1} THEN 1 ELSE 0 END) = 0 AND
                 MAX(CASE WHEN year_item = {year2} THEN 1 ELSE 0 END) = 1 THEN 'New'
            WHEN MAX(CASE WHEN year_item = {year1} THEN 1 ELSE 0 END) = 1 AND
                 MAX(CASE WHEN year_item = {year2} THEN 1 ELSE 0 END) = 0 THEN 'Deleted'
        END AS "Status"
    FROM dataframe
    GROUP BY part_no;
    """.format(years=",".join(map(str, years)), year1=years[0], year2=years[1])

    return query_status


def abnormal_cal_out_house(years, boundaries):
    abnomal_cal = """
    WITH
        dataframe AS (
            SELECT
            o.id,
            o.part_no,
            o.part_name,
            od.price,
            od.source,
            od.year_item
            FROM
            out_house o
            JOIN out_house_detail od ON o.id = od.out_house_item
            WHERE
            od.year_item IN ({years})
    )
    SELECT
        d1.part_no,
        d1.part_name,
        d1.source,
        d1.price AS "Price {year1}",
        d2.price AS "Price {year2}",
        ROUND(
            ((d2.price - d1.price) / NULLIF(d1.price, 0)) * 100,
            2
        ) AS "Gap Price",
        CASE
            WHEN ROUND(
            ((d2.price - d1.price) / NULLIF(d1.price, 0)) * 100,
            2
            ) > {boundaries} THEN 'Abnormal Above {boundaries}%'
            WHEN ROUND(
            ((d2.price - d1.price) / NULLIF(d1.price, 0)) * 100,
            2
            ) < -{boundaries} THEN 'Abnormal Below -{boundaries}%'
        ELSE 'Normal'
    END AS "Status"
    FROM
        dataframe d1
        JOIN dataframe d2 ON d1.id = d2.id
    WHERE
        d1.year_item = {year1}
        AND d2.year_item = {year2}
    ORDER BY
    "Gap Price" DESC;
    """.format(years=",".join(map(str, years)), year1=years[0], year2=years[1], boundaries=boundaries)

    return abnomal_cal


def import_data(conn, df):
    df["part_no"] = df["part_no"].astype(str)

    try:
        cursor = conn.cursor()

        for index, row in df.iterrows():
            try:
                part_no = row["part_no"]
                part_name = row["part_name"]
                price = round(row["price_curr"], 0)
                source = row["source"]
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
                        explanation = ""

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
