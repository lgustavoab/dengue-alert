import {
  access,
} from "node:fs/promises";
import path from "node:path";

export const servingRuntimeVersion =
  "serving-runtime-v1.0.0";

const projectRoot = path.resolve(
  process.cwd(),
  "..",
);

export const canonicalServingRoot =
  path.join(
    projectRoot,
    "data",
    "serving",
  );

export function getServingRuntimeRoot(): string {
  const configuredRoot =
    process.env
      .DENGUE_SERVING_RUNTIME_ROOT;

  if (
    configuredRoot
    && configuredRoot.trim()
  ) {
    return path.resolve(
      configuredRoot,
    );
  }

  return path.join(
    projectRoot,
    "dist",
    servingRuntimeVersion,
  );
}

function isNodeError(
  error: unknown,
): error is NodeJS.ErrnoException {
  return (
    error instanceof Error
    && "code" in error
  );
}

export async function hasServingRuntime(): Promise<boolean> {
  const manifestPath =
    path.join(
      getServingRuntimeRoot(),
      "manifest.json",
    );

  try {
    await access(
      manifestPath,
    );
    return true;
  } catch (error) {
    if (
      isNodeError(
        error,
      )
      && error.code === "ENOENT"
    ) {
      return false;
    }

    throw error;
  }
}

export async function getActiveServingRoot(): Promise<string> {
  if (
    await hasServingRuntime()
  ) {
    return getServingRuntimeRoot();
  }

  return canonicalServingRoot;
}
