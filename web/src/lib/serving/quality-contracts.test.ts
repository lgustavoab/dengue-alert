import { describe, expect, it } from "vitest";

import {
  getClimateCoverage,
  getPopulationCoverage,
  getQualityOverview,
  getSinanPipeline,
  getTerritorialCoverage,
} from "@/lib/serving/server";

describe("contratos de qualidade", () => {
  it("carrega os cinco contratos com schema e período compatíveis", async () => {
    const contracts = await Promise.all([
      getQualityOverview(),
      getSinanPipeline(),
      getTerritorialCoverage(),
      getPopulationCoverage(),
      getClimateCoverage(),
    ]);

    expect(contracts).toHaveLength(5);
    expect(contracts.every((contract) => contract.schema_version === "1.0")).toBe(true);
    expect(contracts.every((contract) => contract.period === "2016-2025")).toBe(true);
    expect(contracts.every((contract) => contract.source.length > 0)).toBe(true);
  });

  it("preserva o funil documentado sem atribuir remoções a NDUPLIC_N", async () => {
    const contract = await getSinanPipeline();
    const filters = contract.data.etapas.filter((step) => step.operation === "filter");
    const documentedRemovals = filters.reduce(
      (total, step) => total + (step.records_removed ?? 0),
      0,
    );
    const duplicateCheck = contract.data.etapas.find((step) => step.id === "duplicate_check");

    expect(duplicateCheck).toMatchObject({
      field: "NDUPLIC_N",
      operation: "validation",
      records_removed: null,
    });
    expect(documentedRemovals).toBe(contract.data.total_remocoes_documentadas);
    expect(contract.data.registros_brutos - documentedRemovals).toBe(
      contract.data.registros_mantidos_apos_filtros,
    );
  });

  it("mantém zero-fill distinto das linhas observadas e preserva casos", async () => {
    const contract = await getSinanPipeline();
    const zeroFill = contract.data.zero_fill;

    expect(zeroFill.linhas_observadas + zeroFill.linhas_preenchidas_com_zero).toBe(
      zeroFill.linhas_finais,
    );
    expect(zeroFill.casos_depois).toBe(zeroFill.casos_antes);
  });

  it("mantém a composição e as exceções territoriais consistentes", async () => {
    const contract = await getTerritorialCoverage();
    const data = contract.data;
    const composition = data.composicao_referencia;

    expect(
      composition.municipios
      + composition.distrito_federal
      + composition.distrito_estadual_fernando_de_noronha,
    ).toBe(data.unidades_territoriais_referencia);
    expect(
      data.codigos_associados_diretamente
      + data.codigos_nao_associados_inicialmente,
    ).toBe(data.codigos_sinan_iniciais);
    expect(
      data.distrito_federal.casos_preservados
      + data.residuais_nao_municipais.casos_excluidos,
    ).toBe(data.casos_nao_associados_inicialmente);
    expect(data.resultado_final.casos_preservados).toBe(16294913);
  });

  it("preserva cobertura populacional e referência do Censo 2022 em 2023", async () => {
    const contract = await getPopulationCoverage();
    const reference2023 = contract.data.referencia_2023;
    const year2023 = contract.data.por_ano.find((year) => year.ano_epidemiologico === 2023);

    expect(contract.data.por_ano).toHaveLength(10);
    expect(contract.data.linhas_sem_populacao).toBe(0);
    expect(contract.data.linhas_populacao_nao_positiva).toBe(0);
    expect(reference2023).toEqual({
      ano_epidemiologico: 2023,
      ano_referencia_populacao: 2022,
      usa_referencia_censo_2022: true,
    });
    expect(year2023?.anos_referencia_populacao).toEqual([2022]);
    expect(year2023?.tipos_populacao).toEqual(["censo_2022_reutilizado_em_2023"]);
  });

  it("mantém cobertura climática e exceção sem inferência epidemiológica", async () => {
    const contract = await getClimateCoverage();
    const data = contract.data;
    const mappedByMethod = Object.values(data.metodos_selecao_grid).reduce(
      (total, value) => total + value,
      0,
    );

    expect(mappedByMethod).toBe(data.unidades_com_mapeamento_climatico);
    expect(data.codigos_excluidos).toEqual(["2605459"]);
    expect(data.municipio_semanas_com_clima + data.municipio_semanas_sem_clima).toBe(2907593);
    expect(data.observacao).toContain("reanálise meteorológica");
  });
});
