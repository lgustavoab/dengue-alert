import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  outputFileTracingIncludes: {
    "/api/serving/territories": [
      "public/data/serving/metadata/territories.json",
      "public/data/serving/historical/municipality/index.json",
      "public/data/serving/prediction/municipality/index.json",
    ],
    "/api/serving/historical/municipality/*": [
      ".runtime/serving/historical/municipalities.ndjson",
      ".runtime/serving/historical/municipalities.index.json",
    ],
    "/api/serving/prediction/municipality/*": [
      ".runtime/serving/prediction/municipalities.ndjson",
      ".runtime/serving/prediction/municipalities.index.json",
    ],
    "/api/serving/prediction/map": [
      ".runtime/serving/prediction/map/index.json",
    ],
    "/api/serving/prediction/map/*/*": [
      ".runtime/serving/prediction/map/h*/se*.json",
    ],
  },
  outputFileTracingExcludes: {
    "/api/serving/territories": [
      "public/data/serving/**/*",
    ],
    "/api/serving/historical/municipality/*": [
      ".runtime/serving/**/*",
    ],
    "/api/serving/prediction/municipality/*": [
      ".runtime/serving/**/*",
    ],
    "/api/serving/prediction/map": [
      ".runtime/serving/**/*",
    ],
    "/api/serving/prediction/map/*/*": [
      ".runtime/serving/**/*",
    ],
  },
};

export default nextConfig;
