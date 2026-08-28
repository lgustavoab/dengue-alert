import {
  access,
} from "node:fs/promises";
import path from "node:path";

export const servingRuntimeVersion =
  "serving-runtime-v1.0.0";

const webRoot = process.cwd();

const projectRoot = path.resolve(
  webRoot,
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
    webRoot,
    ".runtime",
    "serving",
  );
}

export function requiresServingRuntime(): boolean {
  return (
    process.env.VERCEL === "1"
    || process.env.NODE_ENV === "production"
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
    requiresServingRuntime()
    || await hasServingRuntime()
  ) {
    return getServingRuntimeRoot();
  }

  return canonicalServingRoot;
}

export async function shouldUseServingRuntime(): Promise<boolean> {
  return (
    requiresServingRuntime()
    || await hasServingRuntime()
  );
}
