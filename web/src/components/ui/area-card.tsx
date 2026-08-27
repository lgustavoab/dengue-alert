import Link from "next/link";

type AreaCardProps = {
  eyebrow: string;
  title: string;
  description: string;
  href: string;
  metric: string;
  metricLabel: string;
};

export function AreaCard({
  eyebrow,
  title,
  description,
  href,
  metric,
  metricLabel,
}: AreaCardProps) {
  return (
    <article className="area-card">
      <span className="area-card__eyebrow">{eyebrow}</span>

      <div className="area-card__content">
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>

        <div className="area-card__metric">
          <strong>{metric}</strong>
          <span>{metricLabel}</span>
        </div>
      </div>

      <Link
        href={href}
        className="area-card__link"
        aria-label={`Explorar ${title}`}
      >
        Explorar área
        <span aria-hidden="true">→</span>
      </Link>
    </article>
  );
}
