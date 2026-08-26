"use client";

import {
  useMemo,
} from "react";

import {
  FilterBar,
} from "@/components/filters/filter-bar";
import {
  MunicipalityCombobox,
} from "@/components/filters/municipality-combobox";
import {
  SelectFilter,
} from "@/components/filters/select-filter";
import type {
  TerritoryFilterItem,
} from "@/lib/serving/types";

import styles from "./filters.module.css";

type TerritorialFiltersProps = {
  items: TerritoryFilterItem[];
  territoriesLoading: boolean;
  territoriesError: string | null;

  selectedRegion: string;
  selectedUf: string;
  selectedMunicipality: string | null;
  selectedYear: number | null;

  availableYears: number[];

  onRegionChange: (
    value: string,
  ) => void;

  onUfChange: (
    value: string,
  ) => void;

  onMunicipalityChange: (
    value: string | null,
  ) => void;

  onYearChange: (
    value: number | null,
  ) => void;

  onReset: () => void;
};

export function TerritorialFilters({
  items,
  territoriesLoading,
  territoriesError,
  selectedRegion,
  selectedUf,
  selectedMunicipality,
  selectedYear,
  availableYears,
  onRegionChange,
  onUfChange,
  onMunicipalityChange,
  onYearChange,
  onReset,
}: TerritorialFiltersProps) {
  const regionOptions =
    useMemo(
      () => {
        const regions = [
          ...new Set(
            items.map(
              (item) =>
                item.regiao,
            ),
          ),
        ].sort(
          (a, b) =>
            a.localeCompare(
              b,
              "pt-BR",
            ),
        );

        return [
          {
            value: "",
            label:
              "Todas as regiões",
          },
          ...regions.map(
            (region) => ({
              value: region,
              label: region,
            }),
          ),
        ];
      },
      [
        items,
      ],
    );

  const ufItems =
    useMemo(
      () => {
        const filtered =
          selectedRegion
            ? items.filter(
                (item) =>
                  item.regiao
                  === selectedRegion,
              )
            : items;

        const byCode =
          new Map<
            string,
            string
          >();

        for (
          const item
          of filtered
        ) {
          byCode.set(
            item.codigoUfIbge,
            item.nomeUf,
          );
        }

        return [
          ...byCode.entries(),
        ].sort(
          (
            [, nameA],
            [, nameB],
          ) =>
            nameA.localeCompare(
              nameB,
              "pt-BR",
            ),
        );
      },
      [
        items,
        selectedRegion,
      ],
    );

  const ufOptions =
    useMemo(
      () => [
        {
          value: "",
          label:
            "Todas as UFs",
        },
        ...ufItems.map(
          ([
            code,
            name,
          ]) => ({
            value: code,
            label: name,
          }),
        ),
      ],
      [
        ufItems,
      ],
    );

  const municipalityItems =
    useMemo(
      () =>
        items.filter(
          (item) => {
            if (
              selectedRegion
              && item.regiao
              !== selectedRegion
            ) {
              return false;
            }

            if (
              selectedUf
              && item.codigoUfIbge
              !== selectedUf
            ) {
              return false;
            }

            return true;
          },
        ),
      [
        items,
        selectedRegion,
        selectedUf,
      ],
    );

  const yearOptions =
    useMemo(
      () => [
        {
          value: "all",
          label:
            "Todos os anos",
        },
        ...[
          ...availableYears,
        ]
          .sort(
            (a, b) =>
              b - a,
          )
          .map(
            (year) => ({
              value:
                String(
                  year,
                ),
              label:
                String(
                  year,
                ),
            }),
          ),
      ],
      [
        availableYears,
      ],
    );

  const selectedTerritory =
    items.find(
      (item) =>
        item.codigoIbge7
        === selectedMunicipality,
    ) ?? null;

  const hasActiveFilters =
    Boolean(
      selectedRegion
      || selectedUf
      || selectedMunicipality
      || selectedYear,
    );

  let contextLabel =
    "Brasil";

  if (selectedRegion) {
    contextLabel =
      selectedRegion;
  }

  if (selectedUf) {
    const uf =
      ufItems.find(
        ([code]) =>
          code
          === selectedUf,
      );

    if (uf) {
      contextLabel =
        uf[1];
    }
  }

  if (selectedTerritory) {
    contextLabel =
      `${selectedTerritory.nomeMunicipio} — ${selectedTerritory.nomeUf}`;
  }

  const controlsDisabled =
    territoriesLoading
    || Boolean(
      territoriesError,
    );

  return (
    <>
      <FilterBar
        title="Filtros históricos"
        description="Região e UF ajudam a localizar o território. A seleção de município altera o recorte analítico."
        hasActiveFilters={
          hasActiveFilters
        }
        onReset={
          onReset
        }
      >
        <div
          className={`${styles.controlSlot} ${styles.regionControl}`}
        >
          <SelectFilter
            id="historical-region"
            label="Região"
            value={
              selectedRegion
            }
            options={
              regionOptions
            }
            disabled={
              controlsDisabled
            }
            onChange={
              onRegionChange
            }
          />
        </div>

        <div
          className={`${styles.controlSlot} ${styles.ufControl}`}
        >
          <SelectFilter
            id="historical-state"
            label="UF"
            value={
              selectedUf
            }
            options={
              ufOptions
            }
            disabled={
              controlsDisabled
            }
            onChange={
              onUfChange
            }
          />
        </div>

        <div
          className={`${styles.controlSlot} ${styles.municipalityControl}`}
        >
          <MunicipalityCombobox
            items={
              municipalityItems
            }
            selectedCode={
              selectedMunicipality
            }
            disabled={
              controlsDisabled
            }
            onChange={
              onMunicipalityChange
            }
          />
        </div>

        <div
          className={`${styles.controlSlot} ${styles.yearControl}`}
        >
          <SelectFilter
            id="historical-year"
            label="Ano epidemiológico"
            value={
              selectedYear
              === null
                ? "all"
                : String(
                    selectedYear,
                  )
            }
            options={
              yearOptions
            }
            disabled={
              availableYears.length
              === 0
            }
            onChange={(
              value,
            ) =>
              onYearChange(
                value === "all"
                  ? null
                  : Number(
                      value,
                    ),
              )
            }
          />
        </div>
      </FilterBar>

      {territoriesLoading ? (
        <p
          className={
            styles.filterStatus
          }
        >
          Carregando índice territorial…
        </p>
      ) : null}

      {territoriesError ? (
        <p
          className={
            styles.filterError
          }
        >
          {territoriesError}
        </p>
      ) : null}

      <div
        className={
          styles.context
        }
      >
        <span>
          Recorte atual:
        </span>

        <strong>
          {contextLabel}

          {selectedYear
          !== null
            ? ` · ${selectedYear}`
            : ""}
        </strong>
      </div>
    </>
  );
}