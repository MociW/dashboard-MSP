def status_product_two_year(years):
    status_two_year = """
    WITH dataframe AS (
        SELECT DISTINCT i.part_no, ih.year_item
        FROM packing i
        JOIN packing_detail ih ON i.id = ih.packing_item
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


def packing_max_abnormal_cal(years, boundaries):
    max_gap_price = """
    WITH dataframe AS (
        SELECT
            p.id,
            p.part_no,
            p.part_name,
            pd.destination,
            pd.model,
            pd.labor_cost::numeric,
            pd.material_cost::numeric,
            pd.inland_cost::numeric,
            pd.status,
            pd.year_item,
            pe.explanation,
            pe.explained_at
        FROM packing p 
        JOIN packing_detail pd ON p.id = pd.packing_item
        LEFT JOIN (
            SELECT
            packing_detail_id,
            explanation,
            explained_at,
            ROW_NUMBER() OVER (
                PARTITION BY
                packing_detail_id
                ORDER BY
                explained_at DESC
            ) as rn
            FROM
            packing_explanations
        ) pe ON pd.id = pe.packing_detail_id
        AND pe.rn = 1
        WHERE pd.year_item IN ({years})
    ),
    gap_cal AS (
        SELECT 
            t1.part_no,
            t1.part_name,
            t1.destination,
            MAX(t1.labor_cost) AS "Labor Cost {year1}",
            MAX(t1.material_cost) AS "Material Cost {year1}",
            MAX(t1.inland_cost) AS "Inland Cost {year1}",
            MAX(t1.labor_cost + t1.material_cost + t1.inland_cost) AS "Max Total Cost {year1}",

            MAX(t2.labor_cost) AS "Labor Cost {year2}",
            MAX(t2.material_cost) AS "Material Cost {year2}",
            MAX(t2.inland_cost) AS "Inland Cost {year2}",
            MAX(t2.labor_cost + t2.material_cost + t2.inland_cost) AS "Max Total Cost {year2}",
            
            -- Include t2.status since you're using year2's data for comparison
            MAX(t2.status) AS status,
            MAX(t2.explained_at) as explained_at,
            

            ROUND(
                (MAX(t2.labor_cost + t2.material_cost + t2.inland_cost) - MAX(t1.labor_cost + t1.material_cost + t1.inland_cost)) 
                / NULLIF(MAX(t1.labor_cost + t1.material_cost + t1.inland_cost), 0) * 100, 
                2
            ) AS "Gap Total Cost"
        FROM 
            dataframe t1
        JOIN 
            dataframe t2 ON t1.part_no = t2.part_no AND t1.destination = t2.destination
        WHERE 
            t1.year_item = {year1} AND t2.year_item = {year2}
        GROUP BY
            t1.part_no,
            t1.destination,
            t1.part_name
    )
    SELECT
        part_no,
        part_name,
        destination,
        "Labor Cost {year1}",
        "Material Cost {year1}",
        "Inland Cost {year1}",
        "Max Total Cost {year1}",

        "Labor Cost {year2}",
        "Material Cost {year2}",
        "Inland Cost {year2}",
        "Max Total Cost {year2}",

        "Gap Total Cost",
        CASE
            WHEN "Gap Total Cost" > {boundaries} AND status = 'PENDING' THEN 'Abnormal Above {boundaries}%'
            WHEN "Gap Total Cost" < -{boundaries} AND status = 'PENDING' THEN 'Abnormal Below -{boundaries}%'
            ELSE 'Normal'
        END AS "Status",
        CASE
            WHEN status = 'APPROVE' THEN 'Approved'
            WHEN status = 'PENDING' AND explained_at IS NOT NULL THEN 'Disapproved'
            WHEN status = 'PENDING' AND explained_at IS NULL THEN 'Awaiting'
            ELSE 'Awaiting'
        END AS "Explanation Status"
    FROM gap_cal;
    """.format(years=",".join(map(str, years)), year1=years[0], year2=years[1], boundaries=boundaries)

    return max_gap_price
