CREATE TABLE "out_house" (
  "id" UUID PRIMARY KEY DEFAULT (gen_random_uuid()),
  "part_no" VARCHAR UNIQUE NOT NULL,
  "part_name" VARCHAR NOT NULL
);

CREATE TABLE "out_house_detail" (
  "id" SERIAL PRIMARY KEY,
  "out_house_item" UUID REFERENCES "out_house" ("id") ON DELETE CASCADE,
  "price" DECIMAL(10,2),
  "source" VARCHAR,
  "status" VARCHAR DEFAULT 'PENDING',
  "year_item" INT NOT NULL,
  "created_at" TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "out_house_explanations" (
  "id" SERIAL PRIMARY KEY,
  "out_house_detail_id" INT REFERENCES "out_house_detail" ("id") ON DELETE CASCADE, 
  "explanation" TEXT NOT NULL,
  "explained_at" TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "in_house" (
  "id" UUID PRIMARY KEY DEFAULT (gen_random_uuid()),
  "part_no" VARCHAR UNIQUE NOT NULL,
  "part_name" VARCHAR NOT NULL
);

CREATE TABLE "in_house_detail" (
  "id" SERIAL PRIMARY KEY,
  "in_house_item" UUID REFERENCES "in_house" ("id") ON DELETE CASCADE,
  "jsp" DECIMAL(10,2),
  "msp" DECIMAL(10,2),
  "local_oh" DECIMAL(10,2),
  "tooling_oh" DECIMAL(10,2),
  "raw_material" DECIMAL(10,2),
  "labor" DECIMAL(10,2),
  "foh_fixed" DECIMAL(10,2),
  "foh_var" DECIMAL(10,2),
  "unfinish_depre" DECIMAL(10,2),
  "total_process_cost" DECIMAL(10,2),
  "exclusive_investment" DECIMAL(10,2),
  "total_cost" DECIMAL(10,2),
  "status" VARCHAR DEFAULT 'PENDING',
  "year_item" INT NOT NULL,
  "created_at" TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "in_house_explanations" (
  "id" SERIAL PRIMARY KEY,
  "in_house_detail_id" INT REFERENCES "in_house_detail" ("id") ON DELETE CASCADE,
  "explanation" TEXT NOT NULL,
  "explained_at" TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "packing" (
  "id" UUID PRIMARY KEY DEFAULT (gen_random_uuid()),
  "part_no" VARCHAR UNIQUE NOT NULL,
  "part_name" VARCHAR NOT NULL
);

CREATE TABLE "packing_detail" (
  "id" SERIAL PRIMARY KEY,
  "packing_item" UUID REFERENCES "packing" ("id") ON DELETE CASCADE,
  "destination" VARCHAR,
  "model" VARCHAR,
  "labor_cost" DECIMAL(10,2),
  "material_cost" DECIMAL(10,2),
  "inland_cost" DECIMAL(10,2),
  "status" VARCHAR DEFAULT 'PENDING',
  "year_item" INT NOT NULL,
  "created_at" TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "packing_explanations" (
  "id" SERIAL PRIMARY KEY,
  "packing_detail_id" INT REFERENCES "packing_detail" ("id") ON DELETE CASCADE,
  "explanation" TEXT NOT NULL,
  "explained_at" TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);