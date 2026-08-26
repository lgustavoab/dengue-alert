"use client";

import {
  useId,
  useMemo,
  useState,
} from "react";

import type {
  KeyboardEvent,
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
  const inputId =
    useId();

  const listboxId =
    useId();

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

  const [
    activeIndex,
    setActiveIndex,
  ] = useState(-1);

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
    const selectedIndex =
      selectedItem
        ? filteredItems.findIndex(
          (item) =>
            item.codigoIbge7
            === selectedItem.codigoIbge7,
        )
        : -1;

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

    setActiveIndex(
      selectedIndex >= 0
        ? selectedIndex
        : filteredItems.length > 0
          ? 0
          : -1,
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

    setActiveIndex(
      -1,
    );
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

    setActiveIndex(
      0,
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
      false,
    );

    setOpen(
      false,
    );

    setActiveIndex(
      -1,
    );

    onChange(
      item.codigoIbge7,
    );
  }

  function handleKeyDown(
    event: KeyboardEvent<HTMLInputElement>,
  ) {
    if (
      disabled
    ) {
      return;
    }

    if (
      event.key
      === "ArrowDown"
    ) {
      event.preventDefault();

      if (
        filteredItems.length
        === 0
      ) {
        return;
      }

      setOpen(
        true,
      );

      setActiveIndex(
        (current) =>
          current < 0
            ? 0
            : (
              current + 1
            )
            % filteredItems.length,
      );

      return;
    }

    if (
      event.key
      === "ArrowUp"
    ) {
      event.preventDefault();

      if (
        filteredItems.length
        === 0
      ) {
        return;
      }

      setOpen(
        true,
      );

      setActiveIndex(
        (current) =>
          current <= 0
            ? filteredItems.length - 1
            : current - 1,
      );

      return;
    }

    if (
      event.key
      === "Enter"
      && open
      && activeIndex >= 0
      && activeIndex
      < filteredItems.length
    ) {
      event.preventDefault();

      handleSelect(
        filteredItems[
        activeIndex
        ],
      );

      return;
    }

    if (
      event.key
      === "Escape"
      && open
    ) {
      event.preventDefault();

      setOpen(
        false,
      );

      setIsEditing(
        false,
      );

      setQuery("");

      setActiveIndex(
        -1,
      );
    }
  }

  const activeItem =
    open
      && activeIndex >= 0
      && activeIndex
      < filteredItems.length
      ? filteredItems[
      activeIndex
      ]
      : null;

  return (
    <div className={styles.field}>
      <label
        className={styles.label}
        htmlFor={inputId}
      >
        Município
      </label>

      <div
        className={
          styles.combobox
        }
      >
        <input
          id={inputId}
          type="search"
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={open}
          aria-controls={listboxId}
          aria-activedescendant={
            activeItem
              ? `${listboxId}-${activeItem.codigoIbge7}`
              : undefined
          }
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
          onKeyDown={
            handleKeyDown
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
            id={listboxId}
            role="listbox"
            aria-label="Municípios encontrados"
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
                (
                  item,
                  index,
                ) => (
                  <div
                    id={`${listboxId}-${item.codigoIbge7}`}
                    key={
                      item.codigoIbge7
                    }
                    role="option"
                    aria-selected={
                      item.codigoIbge7
                      === selectedCode
                    }
                    data-active={
                      index
                        === activeIndex
                        ? "true"
                        : undefined
                    }
                    className={
                      styles.comboboxOption
                    }
                    onMouseEnter={() =>
                      setActiveIndex(
                        index,
                      )
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
                  </div>
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
