import { createHash } from "node:crypto";
import {
  mkdir,
  mkdtemp,
  readFile,
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
  clearRuntimeIndexCacheForTests,
  getRuntimeMunicipalityPayload,
} from "@/lib/serving/runtime-pack-server";

const temporaryRoots: string[] = [];
const originalRuntimeRoot =
  process.env
    .DENGUE_SERVING_RUNTIME_ROOT;

function sha256(
  payload: Buffer,
): string {
  return createHash(
    "sha256",
  )
    .update(
      payload,
    )
    .digest(
      "hex",
    );
}

async function createRuntimeFixture(): Promise<{
  indexPath: string;
  root: string;
}> {
  const root = await mkdtemp(
    path.join(
      os.tmpdir(),
      "dengue-runtime-reader-",
    ),
  );
  temporaryRoots.push(
    root,
  );
  const collectionRoot =
    path.join(
      root,
      "historical",
    );
  await mkdir(
    collectionRoot,
    {
      recursive: true,
    },
  );
  await writeFile(
    path.join(
      root,
      "manifest.json",
    ),
    "{}\n",
    "utf-8",
  );

  const first = Buffer.from(
    '{"schema_version":"1.0","codigo_ibge_7":"1111111","count":0,"data":{}}',
    "utf-8",
  );
  const second = Buffer.from(
    '{"schema_version":"1.0","codigo_ibge_7":"2222222","count":0,"data":{}}',
    "utf-8",
  );
  const pack = Buffer.concat([
    first,
    Buffer.from(
      "\n",
    ),
    second,
    Buffer.from(
      "\n",
    ),
  ]);
  const packPath =
    path.join(
      collectionRoot,
      "municipalities.ndjson",
    );
  const indexPath =
    path.join(
      collectionRoot,
      "municipalities.index.json",
    );
  await writeFile(
    packPath,
    pack,
  );
  await writeFile(
    indexPath,
    JSON.stringify(
      {
        collection:
          "historical",
        encoding:
          "utf-8",
        entries: {
          "1111111": {
            length:
              first.length,
            offset:
              0,
            sha256:
              sha256(
                first,
              ),
          },
          "2222222": {
            length:
              second.length,
            offset:
              first.length
              + 1,
            sha256:
              sha256(
                second,
              ),
          },
        },
        format:
          "ndjson-offset-v1",
        pack_file:
          "municipalities.ndjson",
        pack_sha256:
          sha256(
            pack,
          ),
        pack_size_bytes:
          pack.length,
        record_count:
          2,
        runtime_version:
          "serving-runtime-v1.0.0",
        schema_version:
          "1.0",
      },
    ),
    "utf-8",
  );
  process.env
    .DENGUE_SERVING_RUNTIME_ROOT =
      root;
  clearRuntimeIndexCacheForTests();

  return {
    indexPath,
    root,
  };
}

afterEach(
  async () => {
    clearRuntimeIndexCacheForTests();

    if (
      originalRuntimeRoot
        === undefined
    ) {
      delete process.env
        .DENGUE_SERVING_RUNTIME_ROOT;
    } else {
      process.env
        .DENGUE_SERVING_RUNTIME_ROOT =
          originalRuntimeRoot;
    }

    await Promise.all(
      temporaryRoots
        .splice(
          0,
        )
        .map(
          (root) => rm(
            root,
            {
              force: true,
              recursive: true,
            },
          ),
        ),
    );
  },
);

describe(
  "runtime municipality pack reader",
  () => {
    it(
      "lê somente o payload indicado pelo segundo range",
      async () => {
        await createRuntimeFixture();

        const result =
          await getRuntimeMunicipalityPayload(
            "historical",
            "2222222",
          );

        expect(
          result,
        ).toEqual(
          {
            available:
              true,
            value: {
              codigo_ibge_7:
                "2222222",
              count:
                0,
              data: {},
              schema_version:
                "1.0",
            },
          },
        );
      },
    );

    it(
      "distingue município ausente de runtime indisponível",
      async () => {
        await createRuntimeFixture();

        await expect(
          getRuntimeMunicipalityPayload(
            "historical",
            "3333333",
          ),
        ).resolves.toEqual(
          {
            available:
              true,
            value:
              null,
          },
        );
      },
    );

    it(
      "rejeita SHA-256 divergente no payload",
      async () => {
        const {
          indexPath,
        } = await createRuntimeFixture();
        const index = JSON.parse(
          await readFile(
            indexPath,
            "utf-8",
          ),
        ) as {
          entries: Record<
            string,
            {
              sha256: string;
            }
          >;
        };
        index.entries[
          "2222222"
        ].sha256 =
          "0".repeat(
            64,
          );
        await writeFile(
          indexPath,
          JSON.stringify(
            index,
          ),
          "utf-8",
        );
        clearRuntimeIndexCacheForTests();

        await expect(
          getRuntimeMunicipalityPayload(
            "historical",
            "2222222",
          ),
        ).rejects.toThrow(
          "SHA-256 divergente",
        );
      },
    );
  },
);
