"use client";

import type {
  ReactNode,
} from "react";

import styles from "./filters.module.css";

type FilterBarProps = {
  title?: string;
  description?: string;
  hasActiveFilters: boolean;
  onReset: () => void;
  children: ReactNode;
};

export function FilterBar({
  title = "Filtros",
  description,
  hasActiveFilters,
  onReset,
  children,
}: FilterBarProps) {
  return (
    <section
      className={styles.bar}
      aria-label="Filtros da visualização"
    >
      <div className={styles.heading}>
        <h2 className={styles.title}>
          {title}
        </h2>

        {description ? (
          <p
            className={
              styles.description
            }
          >
            {description}
          </p>
        ) : null}
      </div>

      <div className={styles.controls}>
        {children}

        <button
          type="button"
          className={styles.reset}
          onClick={onReset}
          disabled={!hasActiveFilters}
        >
          Limpar filtros
        </button>
      </div>
    </section>
  );
}