import ResultCard from './ResultCard.jsx';

export default function ResultSection({ title, items }) {
  if (!items || !items.length) return null;

  return (
    <section className="result-section">
      <h2 className="result-section__title">{title}</h2>
      <div className="result-section__grid">
        {items.map((item, i) => (
          <ResultCard key={i} item={item} />
        ))}
      </div>
    </section>
  );
}
