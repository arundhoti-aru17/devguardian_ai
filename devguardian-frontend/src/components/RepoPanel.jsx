import React, { useRef, useEffect } from "react";

export default function RepoPanel({ watchedRepos, repoPanelOpen, setRepoPanelOpen, panelRef, pillRef, onRemove }) {
  useEffect(() => {
    function onClick(e) {
      if (
        repoPanelOpen &&
        panelRef.current &&
        !panelRef.current.contains(e.target) &&
        pillRef.current &&
        !pillRef.current.contains(e.target)
      ) {
        setRepoPanelOpen(false);
      }
    }

    document.addEventListener("mousedown", onClick);

    return () => {
      document.removeEventListener("mousedown", onClick);
    };
  }, [repoPanelOpen]);

  return (
    {repoPanelOpen && (
      <div
        className="repo-panel"
        ref={panelRef}
      >

        <div className="side-label">Watched repositories</div>

        {watchedRepos.length === 0 ? (
          <div className="no-match" style={{ padding: "6px 4px" }}>
            No repositories connected yet.
          </div>
        ) : (
          watchedRepos.map((r, i) => (
            <div
              className="repo-item"
              key={r.name + i}
            >

              <div>
                <div className="repo-item-name">{r.name}</div>

                <div className="repo-item-meta">
                  watching{" "}
                  {r.branch} · added{" "}
                  {r.added}
                </div>
              </div>

              <button
                className="repo-remove"
                onClick={() => onRemove(i)}
                aria-label={`Stop watching ${r.name}`}
              >
                <X size={13} />
              </button>

            </div>
          ))
        )}

      </div>
    )}
  );
}