import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  outputFileTracingRoot: path.join(__dirname, ".."),
  outputFileTracingIncludes: {
    "/api/serving/territories": [
      "public/data/serving/metadata/territories.json",
      "public/data/serving/historical/municipality/index.json",
      "public/data/serving/prediction/municipality/index.json",
    ],
    "/api/serving/historical/municipality/*": [
      "../dist/serving-runtime-v1.0.0/historical/municipalities.ndjson",
      "../dist/serving-runtime-v1.0.0/historical/municipalities.index.json",
    ],
    "/api/serving/prediction/municipality/*": [
      "../dist/serving-runtime-v1.0.0/prediction/municipalities.ndjson",
      "../dist/serving-runtime-v1.0.0/prediction/municipalities.index.json",
    ],
    "/api/serving/prediction/map": [
      "../dist/serving-runtime-v1.0.0/prediction/map/index.json",
    ],
    "/api/serving/prediction/map/*/*": [
      "../dist/serving-runtime-v1.0.0/prediction/map/h*/se*.json",
    ],
  },
  outputFileTracingExcludes: {
    "/api/serving/territories": [
      "public/data/serving/**/*",
    ],
    "/api/serving/historical/municipality/*": [
      "../data/serving/**/*",
      "../dist/serving-runtime-v1.0.0/**/*",
    ],
    "/api/serving/prediction/municipality/*": [
      "../data/serving/**/*",
      "../dist/serving-runtime-v1.0.0/**/*",
    ],
    "/api/serving/prediction/map": [
      "../data/serving/prediction/map/**/*",
      "../dist/serving-runtime-v1.0.0/**/*",
    ],
    "/api/serving/prediction/map/*/*": [
      "../data/serving/prediction/map/**/*",
      "../dist/serving-runtime-v1.0.0/**/*",
    ],
  },
};

export default nextConfig;
