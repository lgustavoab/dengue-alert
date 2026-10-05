import Link from "next/link";

type AreaCardProps = {
  eyebrow: string;
  title: string;
  description: string;
  href: string;
};

export function AreaCard({
  eyebrow,
  title,
  description,
  href,
}: AreaCardProps) {
  return (
    <article className="area-card">
      <span className="area-card__eyebrow">{eyebrow}</span>

      <div className="area-card__content">
        <h3>{title}</h3>
        <p>{description}</p>
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
