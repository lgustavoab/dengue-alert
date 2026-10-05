import { PREDICTION_HORIZONS } from "@/lib/prediction-selection-utils";
import type {
  PredictionByHorizonContract,
  PredictionEvaluationMetrics,
} from "@/lib/serving/types";

import {
  evaluationTimeLabels,
  formatEvaluationInteger,
  formatEvaluationPercent,
  formatEvaluationScore,
  formatEvaluationThreshold,
} from "./prediction-evaluation-presentation";
import styles from "./prediction-performance.module.css";

type MetricRow = {
  label: string;
  value: (metrics: PredictionEvaluationMetrics) => string;
};

const METRIC_ROWS: MetricRow[] = [
  { label: "Situações avaliadas", value: (m) => formatEvaluationInteger(m.observacoes) },
  { label: "Com risco elevado na semana futura", value: (m) => formatEvaluationInteger(m.positivos) },
  { label: "Sem risco elevado na semana futura", value: (m) => formatEvaluationInteger(m.negativos) },
  { label: "Prevalência do risco elevado", value: (m) => formatEvaluationPercent(m.prevalencia) },
  { label: "Average Precision (AP)", value: (m) => formatEvaluationScore(m.pr_auc_average_precision) },
  { label: "ROC-AUC", value: (m) => formatEvaluationScore(m.roc_auc) },
  { label: "Recall", value: (m) => formatEvaluationPercent(m.recall) },
  { label: "Precisão", value: (m) => formatEvaluationPercent(m.precision) },
  { label: "F1", value: (m) => formatEvaluationPercent(m.f1) },
  { label: "Acurácia balanceada", value: (m) => formatEvaluationPercent(m.balanced_accuracy) },
  { label: "Brier score", value: (m) => formatEvaluationScore(m.brier_score) },
  { label: "Alertas confirmados (TP)", value: (m) => formatEvaluationInteger(m.matriz_confusao.tp) },
  { label: "Alertas não confirmados (FP)", value: (m) => formatEvaluationInteger(m.matriz_confusao.fp) },
  { label: "Riscos não identificados (FN)", value: (m) => formatEvaluationInteger(m.matriz_confusao.fn) },
  { label: "Sem alerta e sem risco elevado observado (TN)", value: (m) => formatEvaluationInteger(m.matriz_confusao.tn) },
];

export function PredictionEvaluationDetails({ evaluation }: { evaluation: PredictionByHorizonContract }) {
  const example = evaluation.horizontes.h1.modelo_final.early_warning;
  const reference = evaluation.horizontes.h1.baseline_persistencia.early_warning;
  return (
    <>
      <p>
        Todas as colunas se referem ao teste retrospectivo de 2025. Os limites de
        alerta foram definidos antes desse teste. Os valores abaixo são os do
        estudo, apenas formatados e arredondados para leitura.
      </p>

      {PREDICTION_HORIZONS.map((key) => {
        const horizon = evaluation.horizontes[key];
        const model = horizon.modelo_final;
        const persistence = horizon.baseline_persistencia;
        const columns = [model.geral, persistence.geral, model.early_warning, persistence.early_warning];
        const captionId = `evaluation-table-${key}-caption`;

        return (
          <div key={key} className={styles.technicalHorizon}>
            <h3>{evaluationTimeLabels[key]} · {key.toUpperCase()}</h3>
            <dl className={styles.parameters}>
              <div>
                <dt>Limite de alerta do modelo</dt>
                <dd>{formatEvaluationThreshold(horizon.threshold_modelo)}</dd>
              </div>
              <div>
                <dt>Limite de alerta da persistência</dt>
                <dd>{formatEvaluationThreshold(persistence.threshold)}</dd>
              </div>
              <div>
                <dt>Situações usadas no treinamento do modelo</dt>
                <dd>{formatEvaluationInteger(model.linhas_treino)}</dd>
              </div>
            </dl>
            <div className={styles.tableScroll} role="region" aria-labelledby={captionId} tabIndex={0}>
              <table className={styles.table}>
                <caption id={captionId}>
                  Comparação de {evaluationTimeLabels[key]}: avaliação geral e antecipação
                </caption>
                <thead>
                  <tr>
                    <th scope="col" rowSpan={2}>Indicador</th>
                    <th scope="colgroup" colSpan={2}>Todas as situações</th>
                    <th scope="colgroup" colSpan={2}>Sem risco elevado na origem</th>
                  </tr>
                  <tr>
                    <th scope="col">Modelo · geral</th>
                    <th scope="col">Persistência · geral</th>
                    <th scope="col">Modelo · antecipação</th>
                    <th scope="col">Persistência · antecipação</th>
                  </tr>
                </thead>
                <tbody>
                  {METRIC_ROWS.map((row) => (
                    <tr key={row.label}>
                      <th scope="row">{row.label}</th>
                      {columns.map((metrics, index) => <td key={index}>{row.value(metrics)}</td>)}
                    </tr>
                  ))}
                  <tr>
                    <th scope="row">Alertas emitidos no recorte de antecipação</th>
                    <td>—</td><td>—</td>
                    <td>{formatEvaluationInteger(model.early_warning.alertas)}</td>
                    <td>{formatEvaluationInteger(persistence.early_warning.alertas)}</td>
                  </tr>
                  <tr>
                    <th scope="row">Proporção de alertas no recorte de antecipação</th>
                    <td>—</td><td>—</td>
                    <td>{formatEvaluationPercent(model.early_warning.proporcao_alertas)}</td>
                    <td>{formatEvaluationPercent(persistence.early_warning.proporcao_alertas)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        );
      })}

      <p>
        — significa não informado ou não aplicável, não zero. A persistência não
        emite alertas no recorte sem risco elevado na origem; sua precisão registrada como
        zero não representa alertas que falharam. As matrizes mostram esse contexto.
      </p>

      <h3>Como ler os indicadores</h3>
      <p>
        Aqui, uma situação é um município em uma semana, não uma pessoa.
        Os exemplos reais abaixo usam o modelo no Brasil em 2025, uma semana
        depois (H1), somente nas situações sem risco elevado na origem.
        Os exemplos ilustrativos servem apenas para explicar a leitura.
      </p>
      <dl className={styles.metricGuide}>
        <dt>Recall — situações de risco identificadas</dt>
        <dd>
          <p><strong>Escala:</strong> 0% a 100%. Maior significa identificar uma parcela maior dos riscos, mas deve ser lido junto da precisão.</p>
          <p><strong>No estudo:</strong> entre as situações que apresentaram risco elevado na semana futura, quantas receberam alerta?</p>
          <p><strong>Exemplo real:</strong> houve alerta em {formatEvaluationInteger(example.matriz_confusao.tp)} de {formatEvaluationInteger(example.positivos)} situações que depois apresentaram risco elevado: recall de {formatEvaluationPercent(example.recall)}.</p>
        </dd>
        <dt>Precisão — alertas que se confirmaram</dt>
        <dd>
          <p><strong>Escala:</strong> 0% a 100%. Maior significa uma proporção menor de alertas não confirmados, mas deve ser lido junto do recall.</p>
          <p><strong>No estudo:</strong> entre os alertas emitidos, quantos corresponderam a risco elevado observado na semana futura? O denominador é diferente do recall.</p>
          <p><strong>Exemplo real:</strong> {example.alertas == null
            ? "a quantidade de alertas não está informada neste recorte."
            : <>dos {formatEvaluationInteger(example.alertas)} alertas, {formatEvaluationInteger(example.matriz_confusao.tp)} se confirmaram: precisão de {formatEvaluationPercent(example.precision)}.</>}</p>
        </dd>
        <dt>Average Precision (AP)</dt>
        <dd>
          <p><strong>Escala:</strong> 0 a 1. Maior é melhor, comparando o mesmo prazo e cenário.</p>
          <p><strong>No estudo:</strong> resume o equilíbrio entre precisão e recall ao variar o limite de alerta,
          avaliando a ordenação das probabilidades. É o indicador armazenado no
          estudo como Average Precision, não uma taxa de acerto nem a área
          trapezoidal da curva precisão–recall. Uma AP de 0,92 não significa 92% de acerto.</p>
          <p><strong>Exemplo real:</strong> AP do modelo: {formatEvaluationScore(example.pr_auc_average_precision)}; da persistência: {formatEvaluationScore(reference.pr_auc_average_precision)}. A frequência de risco também influencia essa leitura; AP não é a chance de uma pessoa ter dengue.</p>
        </dd>
        <dt>ROC-AUC</dt>
        <dd>
          <p><strong>Escala:</strong> 0 a 1. Maior é melhor; 0,5 é a referência de uma ordenação ao acaso.</p>
          <p><strong>No estudo:</strong> mede a capacidade de separar situações com e sem risco elevado ao variar o limite de alerta. Não é a proporção de alertas confirmados.</p>
          <p><strong>Exemplo ilustrativo:</strong> 0,8 indica melhor separação que 0,6 no mesmo cenário, não 80% contra 60% de acerto.</p>
        </dd>
        <dt>F1</dt>
        <dd>
          <p><strong>Escala:</strong> 0% a 100%. Maior é melhor, considerando precisão e recall juntos.</p>
          <p><strong>No estudo:</strong> combina precisão e recall em uma média harmônica. Não deve ser interpretado como porcentagem geral de acerto.</p>
          <p><strong>Exemplo ilustrativo:</strong> precisão de 50% e recall de 50% produzem F1 de 50%; isso não significa acertar metade de todas as situações.</p>
        </dd>
        <dt>Acurácia balanceada</dt>
        <dd>
          <p><strong>Escala:</strong> 0% a 100%. Maior é melhor; as duas classes têm o mesmo peso.</p>
          <p><strong>No estudo:</strong> equilibra a identificação das situações com e sem risco elevado, mesmo quando uma classe é mais frequente.</p>
          <p><strong>Exemplo ilustrativo:</strong> identificar 80% das situações com risco e 60% das situações sem risco resulta em acurácia balanceada de 70%.</p>
        </dd>
        <dt>Brier score</dt>
        <dd>
          <p><strong>Escala:</strong> 0 a 1 nesta avaliação binária. Menor é melhor; zero significa ausência de erro nas probabilidades avaliadas.</p>
          <p><strong>No estudo:</strong> mede o erro quadrático médio entre a probabilidade estimada e o resultado observado. Não é um percentual de acerto.</p>
          <p><strong>Exemplo ilustrativo:</strong> se o risco ocorreu, estimar 0,9 gera erro de 0,01; estimar 0,1 gera erro de 0,81. São erros de uma única situação; o Brier do estudo é a média desses erros.</p>
        </dd>
        <dt>Prevalência</dt>
        <dd>
          <p><strong>Escala:</strong> 0% a 100%. Não existe “maior é melhor” ou “menor é melhor”: é uma descrição dos dados.</p>
          <p><strong>No estudo:</strong> parcela das situações avaliadas que apresentaram risco elevado na semana futura. Não é a prevalência de dengue em pessoas.</p>
          <p><strong>Exemplo real:</strong> {formatEvaluationPercent(example.prevalencia)} das situações deste recorte apresentaram risco elevado na semana futura. Essa frequência ajuda a contextualizar a AP.</p>
        </dd>
      </dl>
      <p>
        AP, ROC-AUC e Brier são apresentados na escala de 0 a 1. As demais taxas
        estão em percentuais. Compare sempre o mesmo indicador, prazo e cenário:
        vantagem em AP não significa superioridade em todas as métricas.
      </p>
    </>
  );
}
