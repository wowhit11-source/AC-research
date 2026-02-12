export default function ResultCard({ item }) {
  const { title = '', url = '', date = '' } = item || {};
  const hasLink = url && url.startsWith('http');

  return (
    <article className="result-card">
      <h3 className="result-card__title">{title || 'Untitled'}</h3>
      {date && <time className="result-card__date">{date}</time>}
      {hasLink && (
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="result-card__link"
        >
          Open link
        </a>
      )}
    </article>
  );
}
