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
            od.status,
            od.year_item,
            oe.explanation,
            oe.explained_at
            FROM
            out_house o
            JOIN out_house_detail od ON o.id = od.out_house_item
            LEFT JOIN (
            SELECT
            out_house_detail_id,
            explanation,
            explained_at,
            ROW_NUMBER() OVER (
                PARTITION BY
                out_house_detail_id
                ORDER BY
                explained_at DESC
            ) as rn
            FROM
            out_house_explanations
        ) oe ON od.id = oe.out_house_detail_id
        AND oe.rn = 1
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
            ) > {boundaries} AND d2.status = 'PENDING' THEN 'Abnormal Above {boundaries}%'
            WHEN ROUND(
            ((d2.price - d1.price) / NULLIF(d1.price, 0)) * 100,
            2
            ) < -{boundaries} AND d2.status = 'PENDING' THEN 'Abnormal Below -{boundaries}%'
        ELSE 'Normal'
    END AS "Status",
    CASE
        WHEN d2.status = 'APPROVE' THEN 'Approved'
        WHEN d2.status = 'PENDING' AND d2.explained_at IS NOT NULL THEN 'Disapproved'
        WHEN d2.status = 'PENDING' AND d2.explained_at IS NULL THEN 'Awaiting'
        ELSE 'Awaiting'
    END AS "Explanation Status"

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


def abnormal_cal_out_house_per_part(years):
    q_abnormal = """
    WITH 
    dataframe AS (
        SELECT
        LEFT(o.part_no, 5) AS "part_num",
        o.part_no,
        o.part_name,
        oh.price,
        oh.source,
        oh.year_item
        FROM
        out_house o
        JOIN out_house_detail oh ON o.id = oh.out_house_item
        WHERE
        oh.year_item IN ({years})
    ),
    
    price_changes AS (
        SELECT
        d1.part_num,
        d1.part_no,
        d1.part_name,
        d1.source,
        d1.price AS "price_{year1}",
        d2.price AS "price_{year2}",
        ROUND(((d2.price - d1.price) / NULLIF(d1.price, 0)) * 100, 2) AS "price_gap_percent"
        FROM
        dataframe d1
        JOIN dataframe d2 ON d1.part_no = d2.part_no
        WHERE
        d1.year_item = {year1}
        AND d2.year_item = {year2}
    ),
    
    part_counts AS (
        SELECT 
        part_num, 
        COUNT(*) AS record_count
        FROM 
        price_changes
        GROUP BY 
        part_num
    ),
    
    valid_parts AS (
        SELECT 
        part_num
        FROM 
        part_counts
        WHERE 
        record_count > 1
    ),
    
    group_stats AS (
        SELECT
        pc.part_num,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price_gap_percent) AS q1,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY price_gap_percent) AS median,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price_gap_percent) AS q3
        FROM 
        price_changes pc
        JOIN
        valid_parts vp ON pc.part_num = vp.part_num
        GROUP BY
        pc.part_num
    ),
    
    iqr_analysis AS (
        SELECT
        pc.part_num,
        pc.part_no,
        pc.part_name,
        pc.source,
        pc.price_{year1},
        pc.price_{year2},
        pc.price_gap_percent,
        gs.q1,
        gs.median,
        gs.q3,
        (gs.q3 - gs.q1) AS iqr,
        (gs.q1 - 1.5 * (gs.q3 - gs.q1)) AS lower_bound,
        (gs.q3 + 1.5 * (gs.q3 - gs.q1)) AS upper_bound
        FROM 
        price_changes pc
        JOIN 
        group_stats gs ON pc.part_num = gs.part_num
    )
    
    SELECT
    part_num,
    part_no,
    part_name,
    source,
    price_{year1},
    price_{year2},
    price_gap_percent,
    q1,
    median,
    q3,
    iqr,
    lower_bound,
    upper_bound,
    CASE
        WHEN price_gap_percent < lower_bound THEN 'Abnormally Low'
        WHEN price_gap_percent > upper_bound THEN 'Abnormally High'
        ELSE 'Normal'
    END AS price_status
    --   CASE
    --     WHEN price_gap_percent < lower_bound THEN price_gap_percent - lower_bound
    --     WHEN price_gap_percent > upper_bound THEN price_gap_percent - upper_bound
    --     ELSE 0
    --   END AS deviation_from_normal_range
    FROM 
    iqr_analysis
    ORDER BY
    part_num
    """.format(years=",".join(map(str, years)), year1=years[0], year2=years[1])

    return q_abnormal
