import { useEffect, useMemo, useState, type ReactNode } from "react";

import { fetchTrustedInterviewDetail } from "../interview/traceApi.js";
import type { TrustedInterviewDetail } from "../interview/traceTypes.js";
import { buildTrustedTraceViewModel } from "../interview/traceViewModel.js";

type LoadState =
  | { status: "loading" }
  | { status: "ready"; detail: TrustedInterviewDetail }
  | { status: "failed"; message: string };

export function TrustedTracePage({
  sessionId,
  ownerId,
}: {
  sessionId: string;
  ownerId: string;
}) {
  const [loadState, setLoadState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setLoadState({ status: "loading" });

    fetchTrustedInterviewDetail({ sessionId, ownerId, signal: controller.signal })
      .then((detail) => setLoadState({ status: "ready", detail }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) {
          return;
        }
        const message = error instanceof Error ? error.message : "trace detail request failed";
        setLoadState({ status: "failed", message });
      });

    return () => controller.abort();
  }, [ownerId, sessionId]);

  const detail = loadState.status === "ready" ? loadState.detail : { session_id: sessionId };
  const viewModel = useMemo(() => buildTrustedTraceViewModel(detail), [detail]);

  return (
    <main className="app-shell trusted-trace-shell">
      <section className="workspace-header" aria-labelledby="trusted-trace-title">
        <div>
          <p className="eyebrow">R1 可信工作台 / trace read surface</p>
          <h1 id="trusted-trace-title">R1 可信 Trace</h1>
          <p className="header-copy">
            展示面试详情中的 trace_summary、RAG citation、evidence gap、评分复盘和 Markdown export
            trace reference。
          </p>
        </div>
        <div className="status-group" aria-label="trace 状态">
          <div className="status-pill">trace_summary: {viewModel.traceStatus}</div>
          <div className="status-pill">owner: {ownerId}</div>
        </div>
      </section>

      {loadState.status === "loading" ? (
        <section className="trace-alert" aria-live="polite">
          正在读取可信 trace...
        </section>
      ) : null}

      {loadState.status === "failed" ? (
        <section className="trace-alert trace-alert-error" aria-live="assertive">
          <strong>Trace 读取失败</strong>
          <span>{loadState.message}</span>
          <span>failed / retryable</span>
        </section>
      ) : null}

      <section className="trusted-grid" aria-label="R1 可信数据摘要">
        <TraceCard title="Trace refs">
          {viewModel.isEmptyTrace ? <p className="empty-copy">旧记录暂无 trace_summary</p> : null}
          <ReferenceGroup label="session" refs={viewModel.sessionRefs} />
          <ReferenceGroup label="turn" refs={viewModel.turnRefs} />
          <ReferenceGroup label="answer" refs={viewModel.answerRefs} />
          <div className="trace-counts" aria-label="trace counts">
            {viewModel.counts.map((item) => (
              <span key={item.label}>
                {item.label}: {item.value}
              </span>
            ))}
          </div>
        </TraceCard>

        <TraceCard title="RAG citation">
          {viewModel.citationItems.length === 0 ? (
            <p className="empty-copy">RAG citation 暂无可展示引用</p>
          ) : (
            <ul className="citation-list">
              {viewModel.citationItems.map((item) => (
                <li key={item.key}>
                  <strong>{item.sourceSummary}</strong>
                  <span>{item.chunkSummary}</span>
                  <span>chunk index: {item.chunkIndex}</span>
                  <span>{item.position}</span>
                </li>
              ))}
            </ul>
          )}
        </TraceCard>

        <TraceCard title="Evidence gap / degraded">
          <TagList items={viewModel.evidenceGapLabels} emptyLabel="暂无 evidence gap" />
          <TagList items={viewModel.statusLabels} emptyLabel="暂无 degraded 状态" />
        </TraceCard>

        <TraceCard title="Review / export refs">
          <ReferenceGroup label="score" refs={viewModel.scoreRefs} />
          <ReferenceGroup label="review" refs={viewModel.reviewRefs} />
          <ReferenceGroup label="export" refs={viewModel.exportRefs} />
        </TraceCard>

        <TraceCard title="Markdown export">
          <div className="export-status">Export status: {viewModel.exportStatus}</div>
          <div>{viewModel.exportRetryable ? "可重试" : "不可重试"}</div>
          <div>failure reason: {viewModel.exportFailureReason}</div>
        </TraceCard>

        <TraceCard title="Request refs">
          {viewModel.requestRefs.length === 0 ? (
            <p className="empty-copy">暂无 request ref</p>
          ) : (
            <ul className="reference-list">
              {viewModel.requestRefs.map((item) => (
                <li key={item.key}>{item.label}</li>
              ))}
            </ul>
          )}
        </TraceCard>
      </section>
    </main>
  );
}

function TraceCard({ title, children }: { title: string; children: ReactNode }) {
  const headingId = `${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-title`;

  return (
    <section className="panel trace-card" aria-labelledby={headingId}>
      <div className="panel-heading">
        <h2 id={headingId}>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function ReferenceGroup({ label, refs }: { label: string; refs: string[] }) {
  return (
    <div className="reference-group">
      <span>{label}</span>
      {refs.length === 0 ? (
        <p className="empty-copy">暂无 {label} ref</p>
      ) : (
        <ul className="reference-list">
          {refs.map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function TagList({ items, emptyLabel }: { items: string[]; emptyLabel: string }) {
  if (items.length === 0) {
    return <p className="empty-copy">{emptyLabel}</p>;
  }

  return (
    <div className="trace-tag-list">
      {items.map((item) => (
        <span key={item}>{item}</span>
      ))}
    </div>
  );
}
