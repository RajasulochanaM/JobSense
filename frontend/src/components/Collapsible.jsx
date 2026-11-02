import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import './Collapsible.css';

/**
 * A card with a clickable header bar that opens and closes its body.
 * Uncontrolled by default (`defaultOpen`); pass `open` + `onOpenChange` to control it.
 * Interactive controls belong in `actions`/children, never inside the header bar itself.
 */
export default function Collapsible({
  id, title, description, defaultOpen = true, open: openProp, onOpenChange, sectionRef, style, children,
}) {
  const [openState, setOpenState] = useState(defaultOpen);
  const controlled = openProp !== undefined;
  const open = controlled ? openProp : openState;
  const bodyId = `${id}-body`;

  const toggle = () => {
    const next = !open;
    if (!controlled) setOpenState(next);
    onOpenChange?.(next);
  };

  return (
    <section id={id} ref={sectionRef} className={`collapse-card ${open ? 'open' : ''}`} style={style}>
      <h2 className="collapse-heading">
        <button type="button" className="collapse-bar" aria-expanded={open} aria-controls={bodyId} onClick={toggle}>
          <span className="collapse-titles">
            <span className="collapse-title">{title}</span>
            {description && <span className="collapse-desc">{description}</span>}
          </span>
          <ChevronDown size={20} className="collapse-chevron" aria-hidden="true" />
        </button>
      </h2>
      <div id={bodyId} className="collapse-body" hidden={!open}>
        {children}
      </div>
    </section>
  );
}
