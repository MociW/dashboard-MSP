-- Create the out_house table with UUID as primary key
CREATE TABLE "out_house" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "part_no" VARCHAR NOT NULL,
    "part_name" VARCHAR NOT NULL,
    UNIQUE ("part_no")  -- Ensure part_no is unique within this table
);

-- Create the out_house_detail table with foreign key reference to out_house
CREATE TABLE "out_house_detail" (
    "id" SERIAL PRIMARY KEY,
    "out_house_item" UUID REFERENCES "out_house" ("id") ON DELETE CASCADE,
    "price" DECIMAL(10, 2),
  	"source" VARCHAR, 
    "year_item" INT NOT NULL,
  	"explanation" TEXT,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "explained_at" TIMESTAMP NULL
);

-- Create the in_house table with UUID as primary key
CREATE TABLE "in_house" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "part_no" VARCHAR NOT NULL,
    "part_name" VARCHAR NOT NULL,
    UNIQUE ("part_no")  -- Ensure part_no is unique within this table
);

-- Create the in_house_detail table with foreign key reference to in_house
CREATE TABLE "in_house_detail" (
    "id" SERIAL PRIMARY KEY,
    "in_house_item" UUID REFERENCES "in_house" ("id") ON DELETE CASCADE,
    "jsp" DECIMAL(10, 2),
    "msp" DECIMAL(10, 2),
    "local_oh" DECIMAL(10, 2),
    "tooling_oh" DECIMAL(10, 2),
    "raw_material" DECIMAL(10, 2),
    "labor" DECIMAL(10, 2),
    "foh_fixed" DECIMAL(10, 2),
    "foh_var" DECIMAL(10, 2),
    "unfinish_depre" DECIMAL(10, 2),
    "total_process_cost" DECIMAL(10, 2),
    "exclusive_investment" DECIMAL(10, 2),
    "total_cost" DECIMAL(10, 2),
    "year_item" INT NOT NULL,
 		"explanation" TEXT,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "explained_at" TIMESTAMP NULL
);

-- Create the packaging table with UUID as primary key
CREATE TABLE "packing" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "part_no" VARCHAR NOT NULL,
    "part_name" VARCHAR NOT NULL,
    UNIQUE ("part_no")  -- Ensure part_no is unique within this table
);

-- Create the packaging_detail table with foreign key reference to packaging
CREATE TABLE "packing_detail" (
    "id" SERIAL PRIMARY KEY,
    "packing_item" UUID REFERENCES "packing" ("id") ON DELETE CASCADE,
  	"destination" VARCHAR,
    "model" VARCHAR,
    "labor_cost" DECIMAL(10, 2),
    "material_cost" DECIMAL(10, 2),
    "inland_cost" DECIMAL(10, 2),
    "year_item" INT NOT NULL,
    "explanation" TEXT,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "explained_at" TIMESTAMP NULL
);

-- DROP SCHEMA public CASCADE;
-- CREATE SCHEMA public;