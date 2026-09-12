"use client";

import { Pause, Play, RotateCcw } from "lucide-react";
import { KeyboardEvent, useEffect, useRef, useState } from "react";

const finalAnimationStep = 7;

export function HeroWorkflow() {
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [pageVisible, setPageVisible] = useState(true);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const syncPreference = () => {
      setReducedMotion(media.matches);
      if (media.matches) {
        setStep(finalAnimationStep);
        setPlaying(false);
      }
    };
    syncPreference();
    media.addEventListener("change", syncPreference);
    return () => media.removeEventListener("change", syncPreference);
  }, []);

  useEffect(() => {
    const onVisibilityChange = () => setPageVisible(!document.hidden);
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () =>
      document.removeEventListener("visibilitychange", onVisibilityChange);
  }, []);

  useEffect(() => {
    if (!playing || !pageVisible || reducedMotion) return;
    const timer = window.setTimeout(() => {
      setStep((current) => {
        if (current >= finalAnimationStep - 1) {
          setPlaying(false);
          return finalAnimationStep;
        }
        return current + 1;
      });
    }, 1450);
    return () => window.clearTimeout(timer);
  }, [pageVisible, playing, reducedMotion, step]);

  const documentStatus =
    step < 2 ? "Uploading" : step < 3 ? "Processing" : "Ready";
  const controlLabel = playing
    ? "Pause animation"
    : step >= finalAnimationStep
      ? "Replay animation"
      : "Play animation";

  function togglePlayback() {
    if (playing) {
      setPlaying(false);
      return;
    }
    if (step >= finalAnimationStep) setStep(0);
    setPlaying(true);
  }

  return (
    <div
      className="hero-product"
      aria-label="Illustrative GroundStack document-to-answer workflow"
    >
      <div className="hero-product-bar">
        <div>
          <span className="product-kicker">Product walkthrough</span>
          <span className="product-caption">Illustrative flow</span>
        </div>
        <button
          className="animation-control"
          type="button"
          onClick={togglePlayback}
          aria-label={controlLabel}
        >
          {playing ? (
            <Pause aria-hidden="true" />
          ) : step >= finalAnimationStep ? (
            <RotateCcw aria-hidden="true" />
          ) : (
            <Play aria-hidden="true" />
          )}
          <span>{controlLabel.replace(" animation", "")}</span>
        </button>
      </div>

      <div className="hero-product-body">
        <div className="demo-upload-panel">
          <div className="demo-file-icon" aria-hidden="true">
            PDF
          </div>
          <div className="demo-file-copy">
            <strong>IT Support Guide.pdf</strong>
            <span>Approved documentation</span>
          </div>
          <span
            className={`demo-status demo-status-${documentStatus.toLowerCase()}`}
          >
            {documentStatus}
          </span>
          <div className="demo-progress" aria-hidden="true">
            <span
              style={{
                width: step === 0 ? "22%" : step === 1 ? "68%" : "100%",
              }}
            />
          </div>
        </div>

        <div
          className="demo-question landing-reveal"
          data-visible={step >= 4 || reducedMotion}
          aria-hidden={step < 4 && !reducedMotion}
        >
          <span>You</span>
          <p>How should I resolve error NET-204?</p>
        </div>

        <div
          className="demo-search landing-reveal"
          data-visible={step >= 5 || reducedMotion}
          aria-hidden={step < 5 && !reducedMotion}
        >
          <span className="demo-search-dot" aria-hidden="true" />
          Searching approved sources
        </div>

        <div
          className="demo-answer landing-reveal"
          data-visible={step >= 6 || reducedMotion}
          aria-hidden={step < 6 && !reducedMotion}
        >
          <span>GroundStack answer</span>
          <p>
            Refresh the active network profile, then verify the connection check
            reports ready. <strong>[S1]</strong>
          </p>
        </div>

        <div
          className="demo-citation landing-reveal"
          data-visible={step >= 7 || reducedMotion}
          aria-hidden={step < 7 && !reducedMotion}
        >
          <div>
            <span>Source [S1]</span>
            <strong>IT Support Guide.pdf</strong>
          </div>
          <p>
            “Refresh the active network profile and confirm the connection check
            returns ready.”
          </p>
        </div>
      </div>
      <div
        className="demo-supported landing-reveal"
        data-visible={step >= 7 || reducedMotion}
        aria-hidden={step < 7 && !reducedMotion}
      >
        <span aria-hidden="true">✓</span> Answer supported by 1 source
      </div>
    </div>
  );
}

const workflowTabs = [
  {
    id: "upload",
    label: "Upload",
    body: "Add approved technical guides, procedures, and internal documentation. GroundStack validates and processes each source before making it searchable.",
  },
  {
    id: "ask",
    label: "Ask",
    body: "Ask a question using natural language. GroundStack searches the available documentation for relevant evidence before generating a response.",
  },
  {
    id: "verify",
    label: "Verify",
    body: "Inspect the documents and excerpts supporting the answer. If the available evidence is insufficient, GroundStack returns an honest limitation instead of inventing information.",
  },
] as const;

type WorkflowTabId = (typeof workflowTabs)[number]["id"];

export function LandingWorkflowTabs() {
  const [activeTab, setActiveTab] = useState<WorkflowTabId>("upload");
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);

  function selectTab(index: number) {
    const normalized = (index + workflowTabs.length) % workflowTabs.length;
    setActiveTab(workflowTabs[normalized].id);
    tabRefs.current[normalized]?.focus();
  }

  function onTabKeyDown(
    event: KeyboardEvent<HTMLButtonElement>,
    index: number,
  ) {
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      event.preventDefault();
      selectTab(index + 1);
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      event.preventDefault();
      selectTab(index - 1);
    } else if (event.key === "Home") {
      event.preventDefault();
      selectTab(0);
    } else if (event.key === "End") {
      event.preventDefault();
      selectTab(workflowTabs.length - 1);
    }
  }

  return (
    <div className="workflow-explorer">
      <div
        className="workflow-tablist"
        role="tablist"
        aria-label="GroundStack workflow"
      >
        {workflowTabs.map((tab, index) => (
          <button
            key={tab.id}
            ref={(element) => {
              tabRefs.current[index] = element;
            }}
            id={`workflow-tab-${tab.id}`}
            className="workflow-tab"
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`workflow-panel-${tab.id}`}
            tabIndex={activeTab === tab.id ? 0 : -1}
            onClick={() => setActiveTab(tab.id)}
            onKeyDown={(event) => onTabKeyDown(event, index)}
          >
            <span>0{index + 1}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {workflowTabs.map((tab, index) => (
        <div
          key={tab.id}
          id={`workflow-panel-${tab.id}`}
          className="workflow-panel"
          role="tabpanel"
          aria-labelledby={`workflow-tab-${tab.id}`}
          tabIndex={0}
          hidden={activeTab !== tab.id}
        >
          <div className="workflow-panel-copy">
            <span className="workflow-panel-step">Step {index + 1}</span>
            <h3>{tab.label}</h3>
            <p>{tab.body}</p>
          </div>
          <WorkflowVisual tab={tab.id} />
        </div>
      ))}
    </div>
  );
}

function WorkflowVisual({ tab }: { tab: WorkflowTabId }) {
  if (tab === "upload") {
    return (
      <div
        className="workflow-visual"
        aria-label="A document progressing from processing to ready"
      >
        <div className="workflow-upload-target">
          <span className="mini-label">Approved source</span>
          <strong>Network operations guide.pdf</strong>
          <div className="workflow-status-row">
            <span>Processing complete</span>
            <strong>Ready</strong>
          </div>
        </div>
        <div className="workflow-excerpt">
          <span>Source excerpt</span>
          <p>
            Verify the active profile before restarting the affected service.
          </p>
        </div>
      </div>
    );
  }

  if (tab === "ask") {
    return (
      <div
        className="workflow-visual"
        aria-label="A question matched to approved evidence"
      >
        <div className="workflow-question">
          How do I restore the network profile?
        </div>
        <div className="workflow-search-line">
          <span className="demo-search-dot" aria-hidden="true" />
          Searching approved sources
        </div>
        <div className="workflow-match">
          <span>Relevant section</span>
          <p>Recovery procedure / Active profile</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="workflow-visual"
      aria-label="A supported answer with a source and an insufficient-evidence example"
    >
      <div className="workflow-answer">
        Restore the approved profile, then run the readiness check.{" "}
        <strong>[S1]</strong>
      </div>
      <div className="workflow-source">
        <span>[S1] Network operations guide.pdf</span>
        <p>“Run the readiness check after restoring the approved profile.”</p>
      </div>
      <div className="workflow-limitation">
        No supporting evidence found for an unrelated policy question.
      </div>
    </div>
  );
}
