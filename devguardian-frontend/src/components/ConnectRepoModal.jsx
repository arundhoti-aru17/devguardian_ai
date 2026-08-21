import React, { useState } from "react";
import { ShieldCheck, GitBranch, X, Plus } from "lucide-react";

export default function ConnectRepoModal({
  modalOpen,
  setModalOpen,
  urlValue,
  setUrlValue,
  branchValue,
  setBranchValue,
  watchedRepos,
  setWatchedRepos,
  showToast,
}) {
  const parseGithubUrl = (raw) => {
    const trimmed = raw
      .trim()
      .replace(/\/+$/, "");

    const m = trimmed.match(
      /^(?:https?:\/\/)?(?:www\.)?github\.com\/([\w.-]+)\/([\w.-]+)$/i
    );

    return m
      ? `${m[1]}/${m[2]}`
      : null;
  };

  const [urlFocused, setUrlFocused] = useState(false);
  const [branchFocused, setBranchFocused] = useState(false);

  const submitRepo = () => {
    const parsed = parseGithubUrl(urlValue);

    if (!parsed) {
      setUrlError("Enter a valid GitHub repository URL, like https://github.com/org/repo");
      return;
    }

    if (
      watchedRepos.some(
        (r) => r.name.toLowerCase() === parsed.toLowerCase()
      )
    ) {
      setUrlError("This repository is already connected.");
      return;
    }

    setWatchedRepos((prev) => [
      {
        name: parsed,
        branch: branchValue.trim() || "main",
        added: "just now",
      },
      ...prev,
    ]);

    setModalOpen(false);

    showToast(
      `Connected ${parsed} — DevGuardian will watch for failed runs.`
    );
  };

  const removeRepo = (i) => {
    setWatchedRepos((prev) =>
      prev.filter((_, idx) => idx !== i)
    );

    showToast(
      `Stopped watching ${watchedRepos[i].name}`
    );
  };

  const showUrlError = urlError ? (
    <div className="field-error">{urlError}</div>
  ) : null;

  return (
    <div
      className="modal-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          setModalOpen(false);
        }
      }}
    >

      <div className="modal">

        <div className="modal-title-row">
          <div className="modal-title">Connect a repository</div>

          <button
            className="modal-close"
            onClick={() => setModalOpen(false)}
          >
            <X size={16} />
          </button>
        </div>

        <div className="modal-sub">
          DevGuardian will listen for failed GitHub Actions runs on this repository and open remediation PRs automatically.
        </div>

        <label className="field-label">Repository URL</label>

        <div className={`field-input-wrap ${urlFocused ? "focused" : ""}`}>
          <GitBranch size={15} />

          <input
            className="field-input"
            placeholder="https://github.com/org/repository"
            value={urlValue}
            onChange={(e) => {
              setUrlValue(e.target.value);

              if (urlError) {
                setUrlError("");
              }
            }}
            onFocus={() => setUrlFocused(true)}
            onBlur={() => setUrlFocused(false)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                submitRepo();
              }
            }}
            autoFocus
          />
        </div>

        {showUrlError}

        <label className="field-label">Branch to watch</label>

        <div className={`field-input-wrap ${branchFocused ? "focused" : ""}`}>
          <GitBranch size={15} />

          <input
            className="field-input"
            placeholder="main"
            value={branchValue}
            onChange={(e) => setBranchValue(e.target.value)}
            onFocus={() => setBranchFocused(true)}
            onBlur={() => setBranchFocused(false)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                submitRepo();
              }
            }}
          />
        </div>

        <div className="modal-actions">

          <button
            className="btn-ghost"
            onClick={() => setModalOpen(false)}
          >
            Cancel
          </button>

          <button
            className="btn-confirm"
            onClick={submitRepo}
          >
            Connect repository
          </button>

        </div>

      </div>

    </div>
  );
}