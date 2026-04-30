import { Alert, Card, Collapse, Descriptions, Empty, List, Spin, Tag, Typography } from "antd";
import { useEffect, useMemo, useState } from "react";

import { fetchTrustedInterviewDetail } from "../interview/traceApi.js";
import type { TrustedInterviewDetail } from "../interview/traceTypes.js";
import { buildTrustedTraceViewModel } from "../interview/traceViewModel.js";

const { Paragraph, Text, Title } = Typography;

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
          <Text className="eyebrow">R1 可信工作台 / trace read surface</Text>
          <Title level={1} id="trusted-trace-title">
            R1 可信 Trace
          </Title>
          <Paragraph className="header-copy">
            展示面试详情中的 trace_summary、RAG citation、evidence gap、评分复盘和 Markdown export
            trace reference。
          </Paragraph>
        </div>
        <div className="status-group" aria-label="trace 状态">
          <Tag color={statusColor(viewModel.traceStatus)}>trace_summary: {viewModel.traceStatus}</Tag>
          <Tag color="blue">owner: {ownerId}</Tag>
        </div>
      </section>

      {loadState.status === "loading" ? (
        <Alert className="trusted-alert" message="正在读取可信 trace..." type="info" showIcon />
      ) : null}

      {loadState.status === "failed" ? (
        <Alert
          className="trusted-alert"
          message="Trace 读取失败"
          description={
            <div className="trusted-alert-detail">
              <Text>{loadState.message}</Text>
              <div>
                <Tag color="error">failed</Tag>
                <Tag color="warning">retryable</Tag>
              </div>
            </div>
          }
          type="error"
          showIcon
        />
      ) : null}

      <Spin spinning={loadState.status === "loading"}>
        <section className="trusted-grid" aria-label="R1 可信数据摘要">
          <Card title="Trace refs" className="trace-card trusted-card">
            {viewModel.isEmptyTrace ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="旧记录暂无 trace_summary" />
            ) : null}
            <Descriptions
              className="trusted-descriptions"
              size="small"
              column={1}
              bordered
              items={[
                {
                  key: "session",
                  label: "session",
                  children: <ReferenceList refs={viewModel.sessionRefs} />,
                },
                {
                  key: "turn",
                  label: "turn",
                  children: <ReferenceList refs={viewModel.turnRefs} />,
                },
                {
                  key: "answer",
                  label: "answer",
                  children: <ReferenceList refs={viewModel.answerRefs} />,
                },
              ]}
            />
            <div className="trusted-tag-row" aria-label="trace counts">
              {viewModel.counts.map((item) => (
                <Tag key={item.label} color="geekblue">
                  {item.label}: {item.value}
                </Tag>
              ))}
            </div>
          </Card>

          <Card title="RAG citation" className="trace-card trusted-card">
            <Collapse
              className="trusted-collapse"
              defaultActiveKey={["citations"]}
              items={[
                {
                  key: "citations",
                  label: "RAG citation 详情",
                  children:
                    viewModel.citationItems.length === 0 ? (
                      <Empty
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                        description="RAG citation 暂无可展示引用"
                      />
                    ) : (
                      <List
                        className="trusted-list"
                        size="small"
                        dataSource={viewModel.citationItems}
                        renderItem={(item) => (
                          <List.Item>
                            <List.Item.Meta
                              title={<Text strong>{item.sourceSummary}</Text>}
                              description={
                                <div className="trusted-list-detail">
                                  <Text>{item.chunkSummary}</Text>
                                  <Text>chunk index: {item.chunkIndex}</Text>
                                  <Text>{item.position}</Text>
                                </div>
                              }
                            />
                          </List.Item>
                        )}
                      />
                    ),
                },
              ]}
            />
          </Card>

          <Card title="Evidence gap / degraded" className="trace-card trusted-card">
            <Alert
              message="Evidence gap"
              description={
                <TagList items={viewModel.evidenceGapLabels} emptyLabel="暂无 evidence gap" />
              }
              type={viewModel.evidenceGapLabels.length > 0 ? "warning" : "info"}
              showIcon
            />
            <Alert
              message="Degraded / failed / retryable"
              description={<TagList items={viewModel.statusLabels} emptyLabel="暂无 degraded 状态" />}
              type={viewModel.statusLabels.includes("failed") ? "error" : "warning"}
              showIcon
            />
            <Collapse
              className="trusted-collapse"
              items={[
                {
                  key: "evidence-gaps",
                  label: "Evidence gap 详情",
                  children: (
                    <Text>{viewModel.evidenceGapLabels.join(" / ") || "暂无 evidence gap"}</Text>
                  ),
                },
              ]}
            />
          </Card>

          <Card title="Review / export refs" className="trace-card trusted-card">
            <Descriptions
              className="trusted-descriptions"
              size="small"
              column={1}
              bordered
              items={[
                {
                  key: "score",
                  label: "score",
                  children: <ReferenceList refs={viewModel.scoreRefs} />,
                },
                {
                  key: "review",
                  label: "review",
                  children: <ReferenceList refs={viewModel.reviewRefs} />,
                },
                {
                  key: "export",
                  label: "export",
                  children: <ReferenceList refs={viewModel.exportRefs} />,
                },
              ]}
            />
          </Card>

          <Card title="Markdown export" className="trace-card trusted-card">
            <div className="export-summary">
              <Text strong>Export status: {viewModel.exportStatus}</Text>
              <Tag color={viewModel.exportRetryable ? "warning" : "default"}>
                {viewModel.exportRetryable ? "可重试" : "不可重试"}
              </Tag>
              <Text>failure reason: {viewModel.exportFailureReason}</Text>
            </div>
          </Card>

          <Card title="Request refs" className="trace-card trusted-card">
            {viewModel.requestRefs.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无 request ref" />
            ) : (
              <List
                className="trusted-list"
                size="small"
                dataSource={viewModel.requestRefs}
                renderItem={(item) => (
                  <List.Item>
                    <Text>{item.label}</Text>
                  </List.Item>
                )}
              />
            )}
          </Card>
        </section>
      </Spin>
    </main>
  );
}

function TagList({ items, emptyLabel }: { items: string[]; emptyLabel: string }) {
  if (items.length === 0) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={emptyLabel} />;
  }

  return (
    <div className="trusted-tag-row">
      {items.map((item) => (
        <Tag key={item} color={statusColor(item)}>
          {item}
        </Tag>
      ))}
    </div>
  );
}

function ReferenceList({ refs }: { refs: string[] }) {
  if (refs.length === 0) {
    return <Text type="secondary">暂无 ref</Text>;
  }

  return (
    <List
      className="trusted-list trusted-reference-list"
      size="small"
      dataSource={refs}
      renderItem={(ref) => (
        <List.Item>
          <Text className="trusted-ref-text">{ref}</Text>
        </List.Item>
      )}
    />
  );
}

function statusColor(status: string): string {
  if (status === "failed" || status === "index_failed") {
    return "error";
  }
  if (status === "degraded" || status === "retryable" || status === "index_pending") {
    return "warning";
  }
  if (status === "available" || status === "completed") {
    return "success";
  }
  if (status === "empty") {
    return "default";
  }
  if (status === "rag_unavailable" || status === "permission_filtered" || status === "no_result") {
    return "processing";
  }
  return "blue";
}
