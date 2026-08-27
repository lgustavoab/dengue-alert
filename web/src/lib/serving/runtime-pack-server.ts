import {
  open,
  readFile,
  stat,
  type FileHandle,
} from "node:fs/promises";
import { createHash } from "node:crypto";
import path from "node:path";

import {
  getServingRuntimeRoot,
  hasServingRuntime,
  servingRuntimeVersion,
} from "@/lib/serving/runtime-paths";

type MunicipalityCollection =
  | "historical"
  | "prediction";

type RuntimeIndexEntry = {
  length: number;
  offset: number;
  sha256: string;
};

type RuntimeIndex = {
  collection: MunicipalityCollection;
  entries: Record<
    string,
    RuntimeIndexEntry
  >;
  packFile: string;
  packSizeBytes: number;
};

export type RuntimePayloadResult =
  | {
    available: false;
  }
  | {
    available: true;
    value: unknown | null;
  };

const ibgeCodePattern =
  /^\d{7}$/;

const sha256Pattern =
  /^[0-9a-f]{64}$/;

const indexCache =
  new Map<
    string,
    Promise<RuntimeIndex>
  >();

function assertObject(
  value: unknown,
  label: string,
): asserts value is Record<
  string,
  unknown
> {
  if (
    typeof value !== "object"
    || value === null
    || Array.isArray(
      value,
    )
  ) {
    throw new TypeError(
      `${label} deve ser um objeto.`,
    );
  }
}

function assertNonNegativeInteger(
  value: unknown,
  label: string,
): asserts value is number {
  if (
    typeof value !== "number"
    || !Number.isInteger(
      value,
    )
    || value < 0
  ) {
    throw new TypeError(
      `${label} deve ser um inteiro não negativo.`,
    );
  }
}

function assertPositiveInteger(
  value: unknown,
  label: string,
): asserts value is number {
  assertNonNegativeInteger(
    value,
    label,
  );

  if (
    value === 0
  ) {
    throw new TypeError(
      `${label} deve ser positivo.`,
    );
  }
}

async function parseRuntimeIndex(
  collection: MunicipalityCollection,
  indexPath: string,
  packPath: string,
): Promise<RuntimeIndex> {
  const rawIndex = await readFile(
    indexPath,
    "utf-8",
  );
  const value = JSON.parse(
    rawIndex,
  ) as unknown;

  assertObject(
    value,
    "Índice municipal de runtime",
  );

  if (
    value.schema_version !== "1.0"
    || value.runtime_version
      !== servingRuntimeVersion
    || value.format
      !== "ndjson-offset-v1"
    || value.encoding
      !== "utf-8"
    || value.collection
      !== collection
  ) {
    throw new Error(
      `Índice municipal de runtime incompatível: ${collection}.`,
    );
  }

  if (
    value.pack_file
      !== path.basename(
        packPath,
      )
  ) {
    throw new Error(
      `Índice municipal aponta para pack divergente: ${collection}.`,
    );
  }

  assertPositiveInteger(
    value.pack_size_bytes,
    "pack_size_bytes",
  );
  assertNonNegativeInteger(
    value.record_count,
    "record_count",
  );
  assertObject(
    value.entries,
    "entries",
  );

  const packMetadata = await stat(
    packPath,
  );

  if (
    packMetadata.size
      !== value.pack_size_bytes
  ) {
    throw new Error(
      `Tamanho do pack municipal divergente: ${collection}.`,
    );
  }

  const entries: Record<
    string,
    RuntimeIndexEntry
  > = {};

  for (
    const [
      code,
      entryValue,
    ]
    of Object.entries(
      value.entries,
    )
  ) {
    if (
      !ibgeCodePattern.test(
        code,
      )
    ) {
      throw new TypeError(
        `Código inválido no índice de runtime: ${code}.`,
      );
    }

    assertObject(
      entryValue,
      `Entrada ${code}`,
    );
    assertNonNegativeInteger(
      entryValue.offset,
      `offset de ${code}`,
    );
    assertPositiveInteger(
      entryValue.length,
      `length de ${code}`,
    );

    if (
      typeof entryValue.sha256
        !== "string"
      || !sha256Pattern.test(
        entryValue.sha256,
      )
    ) {
      throw new TypeError(
        `SHA-256 inválido no índice de runtime: ${code}.`,
      );
    }

    entries[
      code
    ] = {
      length:
        entryValue.length,
      offset:
        entryValue.offset,
      sha256:
        entryValue.sha256,
    };
  }

  if (
    Object.keys(
      entries,
    ).length
      !== value.record_count
  ) {
    throw new Error(
      `record_count divergente no índice de runtime: ${collection}.`,
    );
  }

  let expectedOffset = 0;

  for (
    const [
      code,
      entry,
    ]
    of Object.entries(
      entries,
    ).sort(
      (
        left,
        right,
      ) => left[1].offset
        - right[1].offset,
    )
  ) {
    if (
      entry.offset
        !== expectedOffset
      || entry.offset
        + entry.length
        >= value.pack_size_bytes
    ) {
      throw new Error(
        `Intervalo inválido no índice de runtime: ${code}.`,
      );
    }

    expectedOffset =
      entry.offset
      + entry.length
      + 1;
  }

  if (
    expectedOffset
      !== value.pack_size_bytes
  ) {
    throw new Error(
      `Índice não cobre exatamente o pack: ${collection}.`,
    );
  }

  return {
    collection,
    entries,
    packFile:
      value.pack_file,
    packSizeBytes:
      value.pack_size_bytes,
  };
}

function loadRuntimeIndex(
  collection: MunicipalityCollection,
  indexPath: string,
  packPath: string,
): Promise<RuntimeIndex> {
  const cacheKey =
    `${collection}:${indexPath}:${packPath}`;
  const cached =
    indexCache.get(
      cacheKey,
    );

  if (
    cached
  ) {
    return cached;
  }

  const pending =
    parseRuntimeIndex(
      collection,
      indexPath,
      packPath,
    );

  indexCache.set(
    cacheKey,
    pending,
  );

  pending.catch(
    () => {
      indexCache.delete(
        cacheKey,
      );
    },
  );

  return pending;
}

async function readExactRange(
  file: FileHandle,
  offset: number,
  length: number,
): Promise<Buffer> {
  const buffer = Buffer.allocUnsafe(
    length,
  );
  let bytesRead = 0;

  while (
    bytesRead < length
  ) {
    const result = await file.read(
      buffer,
      bytesRead,
      length - bytesRead,
      offset + bytesRead,
    );

    if (
      result.bytesRead === 0
    ) {
      throw new Error(
        "Pack municipal terminou antes do intervalo indexado.",
      );
    }

    bytesRead +=
      result.bytesRead;
  }

  return buffer;
}

export async function getRuntimeMunicipalityPayload(
  collection: MunicipalityCollection,
  code: string,
): Promise<RuntimePayloadResult> {
  if (
    !await hasServingRuntime()
  ) {
    return {
      available: false,
    };
  }

  const collectionRoot =
    path.join(
      getServingRuntimeRoot(),
      collection,
    );
  const indexPath =
    path.join(
      collectionRoot,
      "municipalities.index.json",
    );
  const packPath =
    path.join(
      collectionRoot,
      "municipalities.ndjson",
    );
  const index =
    await loadRuntimeIndex(
      collection,
      indexPath,
      packPath,
    );
  const entry =
    index.entries[
      code
    ];

  if (
    !entry
  ) {
    return {
      available: true,
      value: null,
    };
  }

  const file = await open(
    packPath,
    "r",
  );

  try {
    const payload =
      await readExactRange(
        file,
        entry.offset,
        entry.length,
      );
    const digest =
      createHash(
        "sha256",
      )
        .update(
          payload,
        )
        .digest(
          "hex",
        );

    if (
      digest
        !== entry.sha256
    ) {
      throw new Error(
        `SHA-256 divergente no payload municipal ${code}.`,
      );
    }

    const decoded =
      new TextDecoder(
        "utf-8",
        {
          fatal: true,
        },
      ).decode(
        payload,
      );

    return {
      available: true,
      value: JSON.parse(
        decoded,
      ) as unknown,
    };
  } finally {
    await file.close();
  }
}

export function clearRuntimeIndexCacheForTests(): void {
  indexCache.clear();
}
