type MetricCardProps = {
  label: string;
  value: string;
  description?: string;
};

export function MetricCard({
  label,
  value,
  description,
}: MetricCardProps) {
  return (
    <article className="metric-card">
      <span className="metric-card__label">
        {label}
      </span>

      <strong className="metric-card__value">
        {value}
      </strong>

      {description ? (
        <p className="metric-card__description">
          {description}
        </p>
      ) : null}
    </article>
  );
}