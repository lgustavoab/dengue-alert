import type { RouteLoadingConfig } from "@/lib/route-state-config";

import styles from "./route-state.module.css";

type RouteLoadingStateProps = {
  config: RouteLoadingConfig;
};

export function RouteLoadingState({
  config,
}: RouteLoadingStateProps) {
  return (
    <main className={styles.wrapper}>
      <section
        className={`${styles.card} ${styles.loadingCard}`}
        role="status"
        aria-live="polite"
        aria-busy="true"
      >
        <span className={styles.eyebrow}>{config.area}</span>
        <h1>{config.loadingTitle}</h1>
        <p>{config.loadingDescription}</p>
        <span className={styles.progress} aria-hidden="true" />
      </section>
    </main>
  );
}
