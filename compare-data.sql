WITH out_house_data AS (SELECT o.part_no,
                          o.part_name,
                          od.price,
                          od.source,
                          od.year_item,
                   FROM out_house o
                            JOIN out_house_detail od ON o.id = od.out_house_item
                   WHERE od.year_item in (2024, 2025)),
    WITH packing_data AS ()