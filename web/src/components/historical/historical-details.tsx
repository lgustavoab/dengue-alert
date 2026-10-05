import type { ReactNode } from "react";

import styles from "./historical-reading.module.css";

export function HistoricalDetails({ title, children }: { title: string; children: ReactNode }) {
  return (
    <details className={styles.details}>
      <summary>{title}</summary>
      <div className={styles.detailsContent}>{children}</div>
    </details>
  );
}
