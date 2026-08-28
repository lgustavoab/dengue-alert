"use client";

import Link from "next/link";

import type { RouteErrorConfig } from "@/lib/route-state-config";

import styles from "./route-state.module.css";

type RouteErrorStateProps = {
  config: RouteErrorConfig;
  onRetry: () => void;
};

export function RouteErrorState({
  config,
  onRetry,
}: RouteErrorStateProps) {
  return (
    <div className={styles.wrapper}>
      <section className={styles.card} role="alert">
        <span className={styles.eyebrow}>{config.area}</span>
        <h1>{config.errorTitle}</h1>
        <p>{config.errorDescription}</p>
        <p className={styles.guidance}>
          Tente novamente. Se a falha persistir, retorne à página inicial.
        </p>
        <div className={styles.actions}>
          <button type="button" onClick={onRetry}>
            Tentar novamente
          </button>
          <Link href="/">Voltar ao início</Link>
        </div>
      </section>
    </div>
  );
}
