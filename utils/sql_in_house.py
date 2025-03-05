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
    WITH dataframe AS (
        SELECT
            i.id,
            i.part_no,
            i.part_name,
            (ih.local_oh + ih.raw_material) AS "lva",
            (ih.jsp + ih.msp) AS "non_lva",
            (ih.tooling_oh + ih.exclusive_investment) AS "tooling",
            ih.total_process_cost AS "process_cost",
            ih.total_cost AS "total_cost",
            ih.year_item
        FROM in_house i
        JOIN in_house_detail ih ON i.id = ih.in_house_item
        WHERE ih.year_item IN ({years})
    )
    SELECT
        d1.part_no,
        d1.part_name,
        d1.lva AS "LVA {year1}",
        d2.lva AS "LVA {year2}",
        ROUND(((d2.lva - d1.lva) / NULLIF(d1.lva, 0)) * 100, 2) AS "Gap LVA %",
        
        d1.non_lva AS "Non LVA {year1}",
        d2.non_lva AS "Non LVA {year2}",
        ROUND(((d2.non_lva - d1.non_lva) / NULLIF(d1.non_lva, 0)) * 100, 2) AS "Gap Non LVA %",
        
        d1.tooling AS "Tooling {year1}",
        d2.tooling AS "Tooling {year2}",
        ROUND(((d2.tooling - d1.tooling) / NULLIF(d1.tooling, 0)) * 100, 2) AS "Gap Tooling %",
        
        d1.process_cost AS "Process Cost {year1}",
        d2.process_cost AS "Process Cost {year2}",
        ROUND(((d2.process_cost - d1.process_cost) / NULLIF(d1.process_cost, 0)) * 100, 2) AS "Gap Process Cost %",
        
        d1.total_cost AS "Total Cost {year1}",
        d2.total_cost AS "Total Cost {year2}",
        ROUND(((d2.total_cost - d1.total_cost) / NULLIF(d1.total_cost, 0)) * 100, 2) AS "Gap Total Cost %",
        
        CASE
            WHEN (ABS(((d2.lva - d1.lva) / NULLIF(d1.lva, 0)) * 100) > {boundaries} AND d2.status='PENDING') OR 
                 (ABS(((d2.non_lva - d1.non_lva) / NULLIF(d1.non_lva, 0)) * 100) > {boundaries} AND d2.status='PENDING') OR 
                 (ABS(((d2.tooling - d1.tooling) / NULLIF(d1.tooling, 0)) * 100) > {boundaries} AND d2.status='PENDING') OR 
                 (ABS(((d2.process_cost - d1.process_cost) / NULLIF(d1.process_cost, 0)) * 100) > {boundaries} AND d2.status='PENDING') OR 
                 (ABS(((d2.total_cost - d1.total_cost) / NULLIF(d1.total_cost, 0)) * 100) > {boundaries} AND d2.status='PENDING')
            THEN 'Abnormal'
            ELSE 'Normal'
        END AS "Status Abnormal"
    FROM dataframe d1
    JOIN dataframe d2 ON d1.id = d2.id
    WHERE d1.year_item = {year1} AND d2.year_item = {year2}
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
        (ih.local_oh + ih.raw_material) AS "lva",
        (ih.jsp + ih.msp) AS "non_lva",
        (ih.tooling_oh + ih.exclusive_investment) AS "tooling",
        (ih.total_process_cost) AS "process_cost",
        (ih.total_cost) AS "total_cost",
        ih.year_item
        FROM
        in_house i
        JOIN in_house_detail ih ON i.id = ih.in_house_item
        WHERE
        year_item IN ({years})
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
        ROUND(((d2.total_cost - d1.total_cost) / (NULLIF(d1.total_cost, 0))) * 100, 2) AS "Gap Total Cost"
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
        WHEN "Gap LVA" > {boundaries} THEN 'Abnormal Above {boundaries}%'
        WHEN "Gap LVA" < -{boundaries} THEN 'Abnormal Below -{boundaries}%'
        ELSE 'Normal'
    END AS "LVA Status",
    
    "Non LVA {year1}",
    "Non LVA {year2}",
    "Gap Non LVA",
    CASE
        WHEN "Gap Non LVA" > {boundaries} THEN 'Abnormal Above {boundaries}%'
        WHEN "Gap Non LVA" < -{boundaries} THEN 'Abnormal Below -{boundaries}%'
        ELSE 'Normal'
    END AS "Non LVA Status",
    
    "Tooling {year1}",
    "Tooling {year2}",
    "Gap Tooling",
    CASE
        WHEN "Gap Tooling" > {boundaries} THEN 'Abnormal Above {boundaries}%'
        WHEN "Gap Tooling" < -{boundaries} THEN 'Abnormal Below -{boundaries}%'
        ELSE 'Normal'
    END AS "Tooling Status",
    
    "Process Cost {year1}",
    "Process Cost {year2}",
    "Gap Process Cost",
    CASE
        WHEN "Gap Process Cost" > {boundaries} THEN 'Abnormal Above {boundaries}%'
        WHEN "Gap Process Cost" < -{boundaries} THEN 'Abnormal Below -{boundaries}%'
        ELSE 'Normal'
    END AS "Process Cost Status",
    
    "Total Cost {year1}",
    "Total Cost {year2}",
    "Gap Total Cost",
    CASE
        WHEN "Gap Total Cost" > {boundaries} THEN 'Abnormal Above {boundaries}%'
        WHEN "Gap Total Cost" < -{boundaries} THEN 'Abnormal Below -{boundaries}%'
        ELSE 'Normal'
    END AS "Total Cost Status",
    
    FROM
    gap_calculation
    """.format(years=",".join(map(str, years)), year1=years[0], year2=years[1], boundaries=boundaries)

    return full_call_abnormal
