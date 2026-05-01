import { Alert, Card, Collapse, Descriptions, Empty, List, Progress, Spin, Tag, Typography } from "antd";
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
          <Text className="eyebrow">R1 可信工作台 / 评分复盘详情</Text>
          <Title level={1} id="trusted-trace-title">
            评分 / 复盘详情
          </Title>
          <Paragraph className="header-copy">
            本场面试的总分、维度理由、证据链、降级态与导出状态。
          </Paragraph>
        </div>
        <div className="status-group" aria-label="trace 状态">
          <Tag color={statusColor(viewModel.traceStatus)}>trace_summary: {viewModel.traceStatus}</Tag>
          <Tag color="geekblue">session: {sessionId}</Tag>
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
        <section className="trusted-section" aria-labelledby="trusted-section-title">
          <div className="trusted-section-heading">
            <Title level={2} id="trusted-section-title">
              可信复盘工作区
            </Title>
            <Text type="secondary">复盘结果、证据链、降级态和导出引用来自本场面试记录。</Text>
          </div>
          <div className="trusted-grid" aria-label="R1 可信数据摘要">
            <div className="trusted-grid-divider">复盘结果</div>
            <Card title="评分 / 复盘" className="trace-card trusted-card">
            {viewModel.scoreTotal === undefined ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="旧记录暂无评分复盘" />
            ) : (
              <div className="export-summary">
                <Text strong>总分 {viewModel.scoreTotal}</Text>
                <Progress percent={viewModel.scoreTotal} size="small" status="active" />
                <Tag color={statusColor(viewModel.scoreStatus)}>score: {viewModel.scoreStatus}</Tag>
              </div>
            )}
            {viewModel.lowConfidence ? (
              <Alert
                message="低置信度复盘"
                description={viewModel.lowConfidenceReason || "证据链不足，复盘结论需谨慎使用。"}
                type="warning"
                showIcon
              />
            ) : null}
            {viewModel.reviewSummary ? (
              <Paragraph className="header-copy">{viewModel.reviewSummary}</Paragraph>
            ) : null}
            <Title level={4}>评分维度</Title>
            {viewModel.dimensionItems.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无评分维度" />
            ) : (
              <List
                className="trusted-list"
                size="small"
                dataSource={viewModel.dimensionItems}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      title={
                        <div className="trusted-tag-row">
                          <Text strong>{item.label}</Text>
                          {item.score !== undefined ? <Tag color="blue">{item.score}</Tag> : null}
                          {item.lowConfidence ? <Tag color="warning">low confidence</Tag> : null}
                        </div>
                      }
                      description={
                        <div className="trusted-list-detail">
                          <Text>{item.reason}</Text>
                          <TagList items={item.citationRefs} emptyLabel="暂无 citation ref" />
                          <TagList items={item.evidenceGapRefs} emptyLabel="暂无 evidence gap" />
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
            <Descriptions
              className="trusted-descriptions"
              size="small"
              column={1}
              bordered
              items={[
                {
                  key: "suggestions",
                  label: "suggestions",
                  children: <TagList items={viewModel.suggestions} emptyLabel="暂无 suggestion" />,
                },
                {
                  key: "weak-areas",
                  label: "weak areas",
                  children: <TagList items={viewModel.weakAreas} emptyLabel="暂无 weak area" />,
                },
              ]}
            />
            </Card>

            <div className="trusted-grid-divider">Trace / RAG 证据链</div>
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

            <div className="trusted-grid-divider">复盘引用与导出</div>
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
          </div>
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
