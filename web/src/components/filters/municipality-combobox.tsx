"use client";

import {
  useMemo,
  useState,
} from "react";

import type {
  TerritoryFilterItem,
} from "@/lib/serving/types";

import styles from "./filters.module.css";

type MunicipalityComboboxProps = {
  items: TerritoryFilterItem[];
  selectedCode: string | null;
  onChange: (
    code: string | null,
  ) => void;
  disabled?: boolean;
};

function normalizeSearchValue(
  value: string,
): string {
  return value
    .normalize("NFD")
    .replace(
      /[\u0300-\u036f]/g,
      "",
    )
    .replace(
      /[^a-zA-Z0-9]+/g,
      " ",
    )
    .toLowerCase()
    .trim();
}

function getMunicipalityLabel(
  item: TerritoryFilterItem,
): string {
  return `${item.nomeMunicipio} — ${item.nomeUf}`;
}

export function MunicipalityCombobox({
  items,
  selectedCode,
  onChange,
  disabled = false,
}: MunicipalityComboboxProps) {
  const [
    query,
    setQuery,
  ] = useState("");

  const [
    open,
    setOpen,
  ] = useState(false);

  const [
    isEditing,
    setIsEditing,
  ] = useState(false);

  const selectedItem =
    useMemo(
      () =>
        items.find(
          (item) =>
            item.codigoIbge7
            === selectedCode,
        ) ?? null,
      [
        items,
        selectedCode,
      ],
    );

  const inputValue =
    isEditing
      ? query
      : selectedItem
        ? getMunicipalityLabel(
            selectedItem,
          )
        : "";

  const filteredItems =
    useMemo(
      () => {
        const normalizedQuery =
          normalizeSearchValue(
            isEditing
              ? query
              : "",
          );

        if (
          normalizedQuery.length
          === 0
        ) {
          return items.slice(
            0,
            40,
          );
        }

        return items
          .filter(
            (item) => {
              const searchable =
                normalizeSearchValue(
                  [
                    item.nomeMunicipio,
                    item.nomeUf,
                    item.codigoIbge7,
                  ].join(
                    " ",
                  ),
                );

              return searchable.includes(
                normalizedQuery,
              );
            },
          )
          .slice(
            0,
            40,
          );
      },
      [
        isEditing,
        items,
        query,
      ],
    );

  function handleFocus() {
    setQuery(
      selectedItem
        ? getMunicipalityLabel(
            selectedItem,
          )
        : "",
    );

    setIsEditing(
      true,
    );

    setOpen(
      true,
    );
  }

  function handleBlur() {
    setOpen(
      false,
    );

    setIsEditing(
      false,
    );

    setQuery("");
  }

  function handleInputChange(
    value: string,
  ) {
    setQuery(
      value,
    );

    setIsEditing(
      true,
    );

    setOpen(
      true,
    );

    if (
      selectedItem
      && value
        !== getMunicipalityLabel(
          selectedItem,
        )
    ) {
      onChange(
        null,
      );
    }
  }

  function handleSelect(
    item: TerritoryFilterItem,
  ) {
    setQuery(
      getMunicipalityLabel(
        item,
      ),
    );

    setIsEditing(
      true,
    );

    setOpen(
      false,
    );

    onChange(
      item.codigoIbge7,
    );
  }

  return (
    <div className={styles.field}>
      <label
        className={styles.label}
        htmlFor="municipality-search"
      >
        Município
      </label>

      <div
        className={
          styles.combobox
        }
      >
        <input
          id="municipality-search"
          type="search"
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={open}
          aria-controls="municipality-options"
          className={
            styles.comboboxInput
          }
          placeholder={
            disabled
              ? "Selecione uma região ou UF"
              : "Digite município ou código IBGE"
          }
          value={
            inputValue
          }
          disabled={
            disabled
          }
          autoComplete="off"
          onFocus={
            handleFocus
          }
          onBlur={
            handleBlur
          }
          onChange={(event) =>
            handleInputChange(
              event.target.value,
            )
          }
        />

        {open
        && !disabled ? (
          <div
            id="municipality-options"
            role="listbox"
            className={
              styles.comboboxOptions
            }
            onMouseDown={(
              event,
            ) =>
              event.preventDefault()
            }
          >
            {filteredItems.length
            > 0 ? (
              filteredItems.map(
                (item) => (
                  <button
                    key={
                      item.codigoIbge7
                    }
                    type="button"
                    role="option"
                    aria-selected={
                      item.codigoIbge7
                      === selectedCode
                    }
                    className={
                      styles.comboboxOption
                    }
                    onClick={() =>
                      handleSelect(
                        item,
                      )
                    }
                  >
                    <span
                      className={
                        styles.comboboxOptionMain
                      }
                    >
                      {
                        item.nomeMunicipio
                      }
                    </span>

                    <span
                      className={
                        styles.comboboxOptionMeta
                      }
                    >
                      {item.nomeUf}
                      {" · "}
                      {item.codigoIbge7}
                      {" · "}
                      {item.anosDisponiveis}
                      {item.anosDisponiveis
                      === 1
                        ? " ano"
                        : " anos"}
                    </span>
                  </button>
                ),
              )
            ) : (
              <div
                className={
                  styles.comboboxEmpty
                }
              >
                Nenhum município encontrado.
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}