type PageIntroProps = {
  eyebrow: string;
  title: string;
  description: string;
  note?: string;
};

export function PageIntro({
  eyebrow,
  title,
  description,
  note,
}: PageIntroProps) {
  return (
    <section className="page-intro">
      <div className="page-intro__content">
        <span className="eyebrow">{eyebrow}</span>

        <h1>{title}</h1>

        <p>{description}</p>

        {note ? <div className="page-intro__note">{note}</div> : null}
      </div>
    </section>
  );
}