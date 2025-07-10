CREATE TABLE "out_house" (
  "id" UUID PRIMARY KEY DEFAULT (gen_random_uuid()),
  "part_no" VARCHAR UNIQUE NOT NULL,
  "part_name" VARCHAR NOT NULL
);

CREATE TABLE "out_house_detail" (
  "id" SERIAL PRIMARY KEY,
  "out_house_item" UUID REFERENCES "out_house" ("id") ON DELETE CASCADE,
  "price" NUMERIC(14,0),
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
  "jsp" NUMERIC(14,0),
  "msp" NUMERIC(14,0),
  "local_oh" NUMERIC(14,0),
  "tooling_oh" NUMERIC(14,0),
  "raw_material" NUMERIC(14,0),
  "labor" NUMERIC(14,0),
  "foh_fixed" NUMERIC(14,0),
  "foh_var" NUMERIC(14,0),
  "unfinish_depre" NUMERIC(14,0),
  "total_process_cost" NUMERIC(14,0),
  "exclusive_investment" NUMERIC(14,0),
  "total_cost" NUMERIC(14,0),
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
  "labor_cost" NUMERIC(14,0),
  "material_cost" NUMERIC(14,0),
  "inland_cost" NUMERIC(14,0),
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