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
        pd.labor_cost,
        pd.material_cost,
        pd.inland_cost,
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
-- First, find the row with max total cost for each part_no/part_name/destination/year
max_rows AS (
    SELECT
        part_no,
        part_name,
        destination,
        year_item,
        labor_cost,
        material_cost,
        inland_cost,
        (labor_cost + material_cost + inland_cost) AS total_cost,
        status,
        explained_at,
        ROW_NUMBER() OVER (
            PARTITION BY part_no, part_name, destination, year_item
            ORDER BY (labor_cost + material_cost + inland_cost) DESC
        ) AS rn
    FROM dataframe
),
-- Get only the max row for each part/part_name/destination/year
max_values AS (
    SELECT
        part_no,
        part_name,
        destination,
        year_item,
        labor_cost,
        material_cost,
        inland_cost,
        total_cost,
        status,
        explained_at
    FROM max_rows
    WHERE rn = 1
),
-- Join the data for both years
gap_cal AS (
    SELECT 
        t1.part_no,
        t1.part_name,
        t1.destination,
        t1.labor_cost AS "Labor Cost {year1}",
        t1.material_cost AS "Material Cost {year1}",
        t1.inland_cost AS "Inland Cost {year1}",
        t1.total_cost AS "Max Total Cost {year1}",

        t2.labor_cost AS "Labor Cost {year2}",
        t2.material_cost AS "Material Cost {year2}",
        t2.inland_cost AS "Inland Cost {year2}",
        t2.total_cost AS "Max Total Cost {year2}",
        
        t2.status AS status_part,
        t2.explained_at as explained_at,
        
        ROUND(
            (t2.total_cost - t1.total_cost) / NULLIF(t1.total_cost, 0) * 100, 
            2
        ) AS "Gap Total Cost",
        
        -- Calculate the status field that we'll need later
        CASE
            WHEN ROUND((t2.total_cost - t1.total_cost) / NULLIF(t1.total_cost, 0) * 100, 2) > {boundaries} 
                 AND t2.status = 'PENDING' THEN 'Abnormal Above {boundaries}%'
            WHEN ROUND((t2.total_cost - t1.total_cost) / NULLIF(t1.total_cost, 0) * 100, 2) < -{boundaries} 
                 AND t2.status = 'PENDING' THEN 'Abnormal Below -{boundaries}%'
            ELSE 'Normal'
        END AS gap_status
    FROM 
        max_values t1
    JOIN 
        max_values t2 ON t1.part_no = t2.part_no AND t1.part_name = t2.part_name AND t1.destination = t2.destination
    WHERE 
        t1.year_item = {year1} AND t2.year_item = {year2}
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
    "Inland Cost {year2}" ,
    "Max Total Cost {year2}",

    "Gap Total Cost",
    gap_status AS "Status",
    CASE
        WHEN TRIM(status_part) = 'APPROVE' THEN 'Approved'
        WHEN TRIM(status_part) = 'PENDING' AND explained_at IS NOT NULL THEN 'Disapproved'
        WHEN TRIM(status_part) = 'PENDING' AND explained_at IS NULL THEN 'Awaiting'
        ELSE 'Awaiting'
    END AS "Explanation Status"
FROM gap_cal;
    """.format(years=",".join(map(str, years)), year1=years[0], year2=years[1], boundaries=boundaries)

    return max_gap_price
