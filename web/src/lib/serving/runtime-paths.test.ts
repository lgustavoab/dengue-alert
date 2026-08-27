import {
  mkdir,
  mkdtemp,
  rm,
  writeFile,
} from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import {
  afterEach,
  describe,
  expect,
  it,
} from "vitest";

import {
  canonicalServingRoot,
  getActiveServingRoot,
  getServingRuntimeRoot,
  shouldUseServingRuntime,
} from "@/lib/serving/runtime-paths";

const originalRuntimeRoot =
  process.env.DENGUE_SERVING_RUNTIME_ROOT;
const originalVercel =
  process.env.VERCEL;
const originalNodeEnvironment =
  process.env.NODE_ENV;
const temporaryRoots: string[] = [];

function setNodeEnvironment(
  value: string | undefined,
): void {
  if (value === undefined) {
    Reflect.deleteProperty(
      process.env,
      "NODE_ENV",
    );
    return;
  }

  Reflect.set(
    process.env,
    "NODE_ENV",
    value,
  );
}

afterEach(async () => {
  if (originalRuntimeRoot === undefined) {
    delete process.env.DENGUE_SERVING_RUNTIME_ROOT;
  } else {
    process.env.DENGUE_SERVING_RUNTIME_ROOT =
      originalRuntimeRoot;
  }

  if (originalVercel === undefined) {
    delete process.env.VERCEL;
  } else {
    process.env.VERCEL = originalVercel;
  }

  if (originalNodeEnvironment === undefined) {
    setNodeEnvironment(
      undefined,
    );
  } else {
    setNodeEnvironment(
      originalNodeEnvironment,
    );
  }

  await Promise.all(
    temporaryRoots.splice(0).map(
      (root) => rm(
        root,
        {
          force: true,
          recursive: true,
        },
      ),
    ),
  );
});

describe("serving runtime paths", () => {
  it("mantém o runtime padrão dentro do web root", () => {
    delete process.env.DENGUE_SERVING_RUNTIME_ROOT;

    expect(getServingRuntimeRoot()).toBe(
      path.join(
        process.cwd(),
        ".runtime",
        "serving",
      ),
    );
  });

  it("preserva override explícito para testes e desenvolvimento", () => {
    const configuredRoot = path.join(
      os.tmpdir(),
      "dengue-explicit-runtime",
    );
    process.env.DENGUE_SERVING_RUNTIME_ROOT =
      configuredRoot;

    expect(getServingRuntimeRoot()).toBe(
      path.resolve(configuredRoot),
    );
  });

  it("não permite fallback canônico no ambiente Vercel", async () => {
    const runtimeRoot = await mkdtemp(
      path.join(os.tmpdir(), "dengue-missing-runtime-"),
    );
    temporaryRoots.push(runtimeRoot);
    await rm(runtimeRoot, { recursive: true });
    process.env.DENGUE_SERVING_RUNTIME_ROOT =
      runtimeRoot;
    process.env.VERCEL = "1";

    await expect(
      shouldUseServingRuntime(),
    ).resolves.toBe(true);
    await expect(
      getActiveServingRoot(),
    ).resolves.toBe(runtimeRoot);
  });

  it("não permite fallback canônico em build de produção", async () => {
    const runtimeRoot = await mkdtemp(
      path.join(os.tmpdir(), "dengue-production-runtime-"),
    );
    temporaryRoots.push(runtimeRoot);
    await rm(runtimeRoot, { recursive: true });
    process.env.DENGUE_SERVING_RUNTIME_ROOT =
      runtimeRoot;
    delete process.env.VERCEL;
    setNodeEnvironment(
      "production",
    );

    await expect(
      shouldUseServingRuntime(),
    ).resolves.toBe(true);
    await expect(
      getActiveServingRoot(),
    ).resolves.toBe(runtimeRoot);
  });

  it("mantém fallback canônico controlado no desenvolvimento", async () => {
    const runtimeRoot = await mkdtemp(
      path.join(os.tmpdir(), "dengue-local-runtime-"),
    );
    temporaryRoots.push(runtimeRoot);
    process.env.DENGUE_SERVING_RUNTIME_ROOT =
      runtimeRoot;
    delete process.env.VERCEL;

    await expect(
      getActiveServingRoot(),
    ).resolves.toBe(canonicalServingRoot);

    await mkdir(runtimeRoot, { recursive: true });
    await writeFile(
      path.join(runtimeRoot, "manifest.json"),
      "{}\n",
      "utf-8",
    );

    await expect(
      getActiveServingRoot(),
    ).resolves.toBe(runtimeRoot);
  });
});
