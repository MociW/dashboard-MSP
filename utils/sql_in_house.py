def status_product_two_year(years):
    status_two_year = """
    WITH dataframe AS (
        SELECT DISTINCT i.part_no, ih.year_item
        FROM in_house i
        JOIN in_house_detail ih ON i.id = ih.in_house_item
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

    return status_two_year


def abnormal_cal(years, boundaries):
    abnormal_cal_query = """
    WITH
    dataframe AS (
        SELECT
        i.id,
        i.part_no,
        i.part_name,
        (ih.local_oh + ih.raw_material) AS lva,
        (ih.jsp + ih.msp) AS non_lva,
        (ih.tooling_oh + ih.exclusive_investment) AS tooling,
        ih.total_process_cost AS process_cost,
        ih.total_cost AS total_cost,
        ih.status,
        ih.year_item,
        ie.explanation,
        ie.explained_at
        FROM
        in_house i
        JOIN in_house_detail ih ON i.id = ih.in_house_item
        LEFT JOIN (
            SELECT
            in_house_detail_id,
            explanation,
            explained_at,
            ROW_NUMBER() OVER (
                PARTITION BY
                in_house_detail_id
                ORDER BY
                explained_at DESC
            ) as rn
            FROM
            in_house_explanations
        ) ie ON ih.id = ie.in_house_detail_id
        AND ie.rn = 1
        WHERE
        ih.year_item IN ({years})
    )
    SELECT
    d1.part_no,
    d1.part_name,
    d1.lva AS "LVA {year1}",
    d2.lva AS "LVA {year2}",
    ROUND(((d2.lva - d1.lva) / NULLIF(d1.lva, 0)) * 100, 2) AS "Gap LVA %",
    d1.non_lva AS "Non LVA {year1}",
    d2.non_lva AS "Non LVA {year2}",
    ROUND(
        ((d2.non_lva - d1.non_lva) / NULLIF(d1.non_lva, 0)) * 100,
        2
    ) AS "Gap Non LVA %",
    d1.tooling AS "Tooling {year1}",
    d2.tooling AS "Tooling {year2}",
    ROUND(
        ((d2.tooling - d1.tooling) / NULLIF(d1.tooling, 0)) * 100,
        2
    ) AS "Gap Tooling %",
    d1.process_cost AS "Process Cost {year1}",
    d2.process_cost AS "Process Cost {year2}",
    ROUND(
        (
        (d2.process_cost - d1.process_cost) / NULLIF(d1.process_cost, 0)
        ) * 100,
        2
    ) AS "Gap Process Cost %",
    d1.total_cost AS "Total Cost {year1}",
    d2.total_cost AS "Total Cost {year2}",
    ROUND(
        (
        (d2.total_cost - d1.total_cost) / NULLIF(d1.total_cost, 0)
        ) * 100,
        2
    ) AS "Gap Total Cost %",
    CASE
        WHEN (
        ABS(((d2.lva - d1.lva) / NULLIF(d1.lva, 0)) * 100) > {boundaries}
        AND d2.status = 'PENDING'
        )
        OR (
        ABS(
            ((d2.non_lva - d1.non_lva) / NULLIF(d1.non_lva, 0)) * 100
        ) > {boundaries}
        AND d2.status = 'PENDING'
        )
        OR (
        ABS(
            ((d2.tooling - d1.tooling) / NULLIF(d1.tooling, 0)) * 100
        ) > {boundaries}
        AND d2.status = 'PENDING'
        )
        OR (
        ABS(
            (
            (d2.process_cost - d1.process_cost) / NULLIF(d1.process_cost, 0)
            ) * 100
        ) > {boundaries}
        AND d2.status = 'PENDING'
        )
        OR (
        ABS(
            (
            (d2.total_cost - d1.total_cost) / NULLIF(d1.total_cost, 0)
            ) * 100
        ) > {boundaries}
        AND d2.status = 'PENDING'
        ) THEN 'Abnormal'
        ELSE 'Normal'
    END AS "Status Abnormal",
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
    """.format(years=",".join(map(str, years)), year1=years[0], year2=years[1], boundaries=boundaries)

    return abnormal_cal_query


def full_abnormal_cal(years, boundaries):
    full_call_abnormal = """
    WITH
    dataframe AS (
        SELECT
        i.id,
        i.part_no,
        i.part_name,
        (ih.local_oh + ih.raw_material) AS lva,
        (ih.jsp + ih.msp) AS non_lva,
        (ih.tooling_oh + ih.exclusive_investment) AS tooling,
        ih.total_process_cost AS process_cost,
        ih.total_cost AS total_cost,
        ih.status,
        ih.year_item,
        ie.explanation,
        ie.explained_at
        FROM
        in_house i
        JOIN in_house_detail ih ON i.id = ih.in_house_item
        LEFT JOIN (
            SELECT
            in_house_detail_id,
            explanation,
            explained_at,
            ROW_NUMBER() OVER (
                PARTITION BY
                in_house_detail_id
                ORDER BY
                explained_at DESC
            ) as rn
            FROM
            in_house_explanations
        ) ie ON ih.id = ie.in_house_detail_id
        AND ie.rn = 1
        WHERE
        ih.year_item IN ({years})
    ),
    gap_calculation AS (
        SELECT
        d1.part_no,
        d1.part_name,
        d1.lva AS "LVA {year1}",
        d2.lva AS "LVA {year2}",
        ROUND(((d2.lva - d1.lva) / (NULLIF(d1.lva, 0))) * 100, 2) AS "Gap LVA",
        
        d1.non_lva AS "Non LVA {year1}",
        d2.non_lva AS "Non LVA {year2}",
        ROUND(((d2.non_lva - d1.non_lva) / (NULLIF(d1.non_lva, 0))) * 100, 2) AS "Gap Non LVA",
        
        d1.tooling AS "Tooling {year1}",
        d2.tooling AS "Tooling {year2}",
        ROUND(((d2.tooling - d1.tooling) / (NULLIF(d1.tooling, 0))) * 100, 2) AS "Gap Tooling",
        
        d1.process_cost AS "Process Cost {year1}",
        d2.process_cost AS "Process Cost {year2}",
        ROUND(((d2.process_cost - d1.process_cost) / (NULLIF(d1.process_cost, 0))) * 100, 2) AS "Gap Process Cost",
        
        d1.total_cost AS "Total Cost {year1}",
        d2.total_cost AS "Total Cost {year2}",
        ROUND(((d2.total_cost - d1.total_cost) / (NULLIF(d1.total_cost, 0))) * 100, 2) AS "Gap Total Cost",
        
        d2.status,
        d2.explained_at
        FROM
        dataframe d1
        JOIN dataframe d2 ON d1.id = d2.id
        WHERE
        d1.year_item = {year1}
        AND d2.year_item = {year2}
    )
    SELECT
    part_no,
    part_name,
    "LVA {year1}",
    "LVA {year2}",
    "Gap LVA",
    CASE
        WHEN "Gap LVA" > {boundaries} AND status = 'PENDING' THEN 'Abnormal Above {boundaries}%'
        WHEN "Gap LVA" < -{boundaries} AND status = 'PENDING' THEN 'Abnormal Below -{boundaries}%'
        ELSE 'Normal'
    END AS "LVA Status",
    
    "Non LVA {year1}",
    "Non LVA {year2}",
    "Gap Non LVA",
    CASE
        WHEN "Gap Non LVA" > {boundaries} AND status = 'PENDING' THEN 'Abnormal Above {boundaries}%'
        WHEN "Gap Non LVA" < -{boundaries} AND status = 'PENDING' THEN 'Abnormal Below -{boundaries}%'
        ELSE 'Normal'
    END AS "Non LVA Status",
    
    "Tooling {year1}",
    "Tooling {year2}",
    "Gap Tooling",
    CASE
        WHEN "Gap Tooling" > {boundaries} AND status = 'PENDING' THEN 'Abnormal Above {boundaries}%'
        WHEN "Gap Tooling" < -{boundaries} AND status = 'PENDING' THEN 'Abnormal Below -{boundaries}%'
        ELSE 'Normal'
    END AS "Tooling Status",
    
    "Process Cost {year1}",
    "Process Cost {year2}",
    "Gap Process Cost",
    CASE
        WHEN "Gap Process Cost" > {boundaries} AND status = 'PENDING' THEN 'Abnormal Above {boundaries}%'
        WHEN "Gap Process Cost" < -{boundaries} AND status = 'PENDING' THEN 'Abnormal Below -{boundaries}%'
        ELSE 'Normal'
    END AS "Process Cost Status",
    
    "Total Cost {year1}",
    "Total Cost {year2}",
    "Gap Total Cost",
    CASE
        WHEN "Gap Total Cost" > {boundaries} AND status = 'PENDING' THEN 'Abnormal Above {boundaries}%'
        WHEN "Gap Total Cost" < -{boundaries} AND status = 'PENDING' THEN 'Abnormal Below -{boundaries}%'
        ELSE 'Normal'
    END AS "Total Cost Status",
    CASE
        WHEN status = 'APPROVE' THEN 'Approved'
        WHEN status = 'PENDING' AND explained_at IS NOT NULL THEN 'Disapproved'
        WHEN status = 'PENDING' AND explained_at IS NULL THEN 'Awaiting'
        ELSE 'Awaiting'
    END AS "Explanation Status"
    
    FROM
    gap_calculation
    """.format(years=",".join(map(str, years)), year1=years[0], year2=years[1], boundaries=boundaries)

    return full_call_abnormal


def abnormal_cal_in_house_per_part(years):
    query = """
            WITH dataframe AS (SELECT LEFT(i.part_no, 5)                        AS "part_num",
                              i.part_no,
                              i.part_name,
                              (ih.local_oh + ih.raw_material)           AS lva,
                              (ih.jsp + ih.msp)                         AS non_lva,
                              (ih.tooling_oh + ih.exclusive_investment) AS tooling,
                              ih.total_process_cost                     AS process_cost,
                              ih.total_cost                             AS total_cost,
                              ih.year_item
                       FROM in_house i
                                JOIN in_house_detail ih ON i.id = ih.in_house_item
                       WHERE ih.year_item IN ({years})),
    
         price_changes AS (SELECT COALESCE(d1.part_num, d2.part_num) AS part_num,
                                  COALESCE(d1.part_no, d2.part_no)   AS part_no,
                                  COALESCE(d1.part_name, d2.part_name) AS part_name,
                                  d1.lva          AS lva_{year1},
                                  d2.lva          AS lva_{year2},
                                  d1.non_lva      AS non_lva_{year1},
                                  d2.non_lva      AS non_lva_{year2},
                                  d1.tooling      AS tooling_{year1},
                                  d2.tooling      AS tooling_{year2},
                                  d1.process_cost AS process_{year1},
                                  d2.process_cost AS process_{year2},
                                  d1.total_cost   AS total_cost_{year1},
                                  d2.total_cost   AS total_cost_{year2},
                                  CASE 
                                      WHEN d1.total_cost IS NULL OR d2.total_cost IS NULL THEN NULL
                                      ELSE ROUND(((d2.total_cost - d1.total_cost) / NULLIF(d1.total_cost, 0)) * 100, 2)
                                  END AS "price_gap_percent"
                           FROM (SELECT * FROM dataframe WHERE year_item = {year1}) d1
                                    RIGHT JOIN 
                                (SELECT * FROM dataframe WHERE year_item = {year2}) d2 
                                ON d1.part_no = d2.part_no),
    
         part_counts AS (SELECT part_num,
                                COUNT(*) AS record_count
                         FROM price_changes
                         GROUP BY part_num),
    
         valid_parts AS (SELECT part_num
                         FROM part_counts
                         WHERE record_count > 1),
    
         group_stats AS (SELECT pc.part_num,
                                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price_gap_percent) AS q1,
                                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY price_gap_percent) AS median,
                                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price_gap_percent) AS q3
                         FROM price_changes pc
                                  JOIN
                              valid_parts vp ON pc.part_num = vp.part_num
                         WHERE pc.price_gap_percent IS NOT NULL
                         GROUP BY pc.part_num),
    
         iqr_analysis AS (SELECT pc.part_num,
                                 pc.part_no,
                                 pc.part_name,
                                 pc.lva_{year1},
                                 pc.lva_{year2},
                                 pc.non_lva_{year1},
                                 pc.non_lva_{year2},
                                 pc.process_{year1},
                                 pc.process_{year2},
                                 pc.tooling_{year1},
                                 pc.tooling_{year2},
                                 pc.total_cost_{year1},
                                 pc.total_cost_{year2},
                                 pc.price_gap_percent,
                                 gs.q1,
                                 gs.median,
                                 gs.q3,
                                 (gs.q3 - gs.q1)                 AS iqr,
                                 (gs.q1 - 1.5 * (gs.q3 - gs.q1)) AS lower_bound,
                                 (gs.q3 + 1.5 * (gs.q3 - gs.q1)) AS upper_bound
                          FROM price_changes pc
                                   LEFT JOIN
                               group_stats gs
                               ON pc.part_num = gs.part_num)
    
    SELECT part_num,
           part_no,
           part_name,
           lva_{year1},
           lva_{year2},
           non_lva_{year1},
           non_lva_{year2},
           process_{year1},
           process_{year2},
           tooling_{year1},
           tooling_{year2},
           total_cost_{year1},
           total_cost_{year2},
           price_gap_percent,
           q1,
           median,
           q3,
           iqr,
           lower_bound,
           upper_bound,
           CASE
               WHEN price_gap_percent IS NULL THEN 'No Comparison Available'
               WHEN price_gap_percent < lower_bound THEN 'Abnormally Low'
               WHEN price_gap_percent > upper_bound THEN 'Abnormally High'
               ELSE 'Normal'
               END AS price_status,
           CASE
               WHEN price_gap_percent IS NULL THEN NULL
               WHEN price_gap_percent < lower_bound THEN price_gap_percent - lower_bound
               WHEN price_gap_percent > upper_bound THEN price_gap_percent - upper_bound
               ELSE 0
               END AS deviation_from_normal_range
    FROM iqr_analysis
    ORDER BY part_num
    """.format(years=",".join(map(str, years)), year1=years[0], year2=years[1])

    return query
