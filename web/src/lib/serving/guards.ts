function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function assertServingContract(
    value: unknown,
    contractName: string,
): asserts value is Record<string, unknown> {
    if (!isRecord(value)) {
        throw new TypeError(
            `Contrato de serving inválido: ${contractName} não é um objeto JSON.`,
        );
    }

    if (value.schema_version !== "1.0") {
        throw new Error(
            `Contrato de serving incompatível: ${contractName} possui schema_version diferente de 1.0.`,
        );
    }
}

export function assertNumber(
    value: unknown,
    fieldName: string,
): asserts value is number {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        throw new TypeError(
            `Campo numérico inválido no serving: ${fieldName}.`,
        );
    }
}

export function assertString(
    value: unknown,
    fieldName: string,
): asserts value is string {
    if (typeof value !== "string") {
        throw new TypeError(
            `Campo textual inválido no serving: ${fieldName}.`,
        );
    }
}