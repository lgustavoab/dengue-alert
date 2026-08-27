import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const repositoryRoot = path.dirname(webRoot);
const bootstrapScript = path.join(
  repositoryRoot,
  "scripts",
  "bootstrap_serving_runtime.py",
);
const archivePath = process.env.DENGUE_SERVING_RUNTIME_ARCHIVE;
const pythonCommands = process.platform === "win32"
  ? ["python", "py"]
  : ["python3", "python"];

let pythonFound = false;

for (const command of pythonCommands) {
  const result = spawnSync(
    command,
    [
      bootstrapScript,
      ...(archivePath
        ? ["--archive", path.resolve(repositoryRoot, archivePath)]
        : []),
      "--sync-web",
    ],
    {
      cwd: repositoryRoot,
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
        PYTHONUTF8: "1",
      },
      stdio: "inherit",
    },
  );

  if (result.error?.code === "ENOENT") {
    continue;
  }

  if (result.error) {
    throw result.error;
  }

  pythonFound = true;

  if (result.status !== 0) {
    process.exitCode = result.status ?? 1;
  }

  break;
}

if (!pythonFound) {
  throw new Error(
    "Python 3 não encontrado; instale python3 ou python para preparar o serving.",
  );
}
