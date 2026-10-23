import { useState } from 'react';
import './BarList.css';

/**
 * Single-series horizontal bar chart (magnitude comparison across categories).
 * - one hue (burgundy); single series, so no legend - the card title names it
 * - bars <= 24px thick, 4px rounded data-end, square at the baseline
 * - every value is labelled at the bar tip in text ink, so the hover/focus tooltip
 *   only enhances; a table view exposes the same data without the chart
 */
export default function BarList({ data, labelKey = 'label', valueKey = 'value', unit = '', title, emptyText = 'No data yet.' }) {
  const [asTable, setAsTable] = useState(false);
  const [active, setActive] = useState(null);
  if (!data?.length) return <p className="small muted">{emptyText}</p>;
  const max = Math.max(...data.map((d) => Number(d[valueKey]) || 0), 1);
  const fmt = (v) => `${Number(v).toLocaleString('en-IN')}${unit}`;

  return (
    <div className="barlist">
      <div className="barlist-toolbar">
        <button type="button" className="btn btn-ghost btn-sm" onClick={() => setAsTable((t) => !t)} aria-pressed={asTable}>
          {asTable ? 'Show chart' : 'Show table'}
        </button>
      </div>
      {asTable ? (
        <table className="table">
          <caption className="sr-only">{title}</caption>
          <thead><tr><th scope="col">Category</th><th scope="col" style={{ textAlign: 'right' }}>Value</th></tr></thead>
          <tbody>
            {data.map((d) => (
              <tr key={d[labelKey]}><td>{d[labelKey]}</td><td style={{ textAlign: 'right' }} className="tabular">{fmt(d[valueKey])}</td></tr>
            ))}
          </tbody>
        </table>
      ) : (
        <ul className="barlist-rows list-plain" aria-label={title}>
          {data.map((d, i) => {
            const v = Number(d[valueKey]) || 0;
            return (
              <li key={d[labelKey]} className={`barlist-row ${active === i ? 'active' : ''}`} tabIndex={0}
                onPointerEnter={() => setActive(i)} onPointerLeave={() => setActive(null)}
                onFocus={() => setActive(i)} onBlur={() => setActive(null)}
                aria-label={`${d[labelKey]}: ${fmt(v)}`}>
                <span className="barlist-label">{d[labelKey]}</span>
                <span className="barlist-track">
                  <span className="barlist-bar" style={{ width: `${Math.max((v / max) * 100, v > 0 ? 1.5 : 0)}%` }} />
                  <span className="barlist-value">{fmt(v)}</span>
                  {active === i && (
                    <span className="barlist-tip" role="tooltip">
                      <strong>{fmt(v)}</strong><span>{d[labelKey]}</span>
                    </span>
                  )}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
