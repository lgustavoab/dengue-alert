import type { PredictionByHorizonContract } from "@/lib/serving/types";

import { PredictionEarlyWarning } from "./prediction-early-warning";
import { PredictionEvaluationDetails } from "./prediction-evaluation-details";
import {
  formatEvaluationPercent,
} from "./prediction-evaluation-presentation";
import styles from "./prediction-performance.module.css";

export function PredictionPerformance({ evaluation }: { evaluation: PredictionByHorizonContract }) {
  const h1 = evaluation.horizontes.h1.modelo_final;

  return (
    <section className={styles.section} aria-labelledby="prediction-performance-title">
      <div className={styles.heading}>
        <span className={styles.eyebrow}>Avaliação nacional · teste de 2025</span>
        <h2 id="prediction-performance-title">Avaliar o modelo</h2>
        <p>
          Estes resultados resumem todos os municípios incluídos no teste. Não
          mudam com os filtros da consulta e não medem o desempenho da cidade
          selecionada.
        </p>
      </div>

      <div className={styles.scopes}>
        <div>
          <h3>Todas as situações avaliadas</h3>
          <p>
            A avaliação geral inclui semanas com e sem risco elevado no ponto de
            partida. Parte dos resultados envolve risco que já estava presente.
          </p>
        </div>
        <div>
          <h3>Sem risco elevado no ponto de partida</h3>
          <p>
            O recorte de antecipação pergunta se o modelo identificou risco futuro
            quando o município ainda não apresentava risco elevado. É uma tarefa
            diferente da avaliação geral.
          </p>
        </div>
      </div>
      <p className={styles.units}>
        Uma situação é um município em uma semana de referência. As contagens não
        representam pessoas nem municípios distintos. Cada prazo é avaliado separadamente.
      </p>

      <PredictionEarlyWarning evaluation={evaluation} />

      <div className={styles.interpretation}>
        <h3>Por que separar esses cenários?</h3>
        <p>
          Para uma semana depois, o modelo identificou {formatEvaluationPercent(h1.geral.recall)} das
          situações com risco elevado na avaliação geral. Considerando apenas
          situações sem risco elevado no ponto de partida, essa parcela foi {formatEvaluationPercent(h1.early_warning.recall)}.
          O resultado geral não deve ser interpretado como capacidade de antecipar risco novo.
        </p>
        <h3>O que usamos como comparação?</h3>
        <p>
          Comparamos o modelo com uma regra simples: o estado da semana de referência
          continua igual no futuro. Essa regra é chamada de persistência. Se não
          havia risco elevado na origem, ela não emite alerta; por isso, não
          antecipa risco nesse recorte. Os resultados completos das duas estratégias
          estão nas tabelas abaixo.
        </p>
      </div>

      <p className={styles.note}>
        O modelo identificou parte das situações futuras de risco, mas também emitiu
        alertas não confirmados e deixou de identificar outras situações. Este teste
        usa dados históricos consolidados de um único ano, 2025. O resultado nacional
        não garante o mesmo desempenho em cada município nem em uso atual.
      </p>

      <details className={styles.technicalDetails}>
        <summary>Ver métricas completas e comparação com a persistência</summary>
        <PredictionEvaluationDetails evaluation={evaluation} />
      </details>
    </section>
  );
}
