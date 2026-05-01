import { Alert, Button, Card, Empty, List, Space, Tag, Typography } from "antd";
import { useEffect, useMemo, useState } from "react";

import { workbenchRoutePages } from "../appContent.js";
import { fetchInterviewHistory } from "../interview/traceApi.js";
import type { InterviewHistoryResponse } from "../interview/traceTypes.js";
import { buildHistoryViewModel } from "../interview/historyViewModel.js";
import { WorkbenchNav } from "./WorkbenchNav.js";

const { Paragraph, Text, Title } = Typography;

export type WorkbenchRoutePageKind = "jobs" | "resumes" | "interviews" | "interviewsNew" | "reviews";

type HistoryLoadState =
  | { status: "loading" }
  | { status: "ready"; response: InterviewHistoryResponse }
  | { status: "failed"; message: string };

export function WorkbenchRoutePage({
  kind,
  ownerId,
}: {
  kind: WorkbenchRoutePageKind;
  ownerId: string;
}) {
  if (kind === "interviews") {
    return <InterviewHistoryPage ownerId={ownerId} />;
  }
  if (kind === "reviews") {
    return <ReviewListPage ownerId={ownerId} />;
  }

  const page = workbenchRoutePages[kind];

  return (
    <main className="app-shell workbench-route-shell">
      <WorkbenchNav />
      <section className="workspace-header" aria-labelledby={`${kind}-title`}>
        <div>
          <Text className="eyebrow">{page.eyebrow}</Text>
          <Title level={1} id={`${kind}-title`}>
            {page.title}
          </Title>
          <Paragraph className="header-copy">{page.copy}</Paragraph>
        </div>
        <div className="status-group" aria-label={`${page.title} 当前阶段`}>
          <Tag color="blue">R1B-01</Tag>
          <Tag color="geekblue">真实 route</Tag>
        </div>
      </section>

      <section className="home-section" aria-labelledby={`${kind}-stage-title`}>
        <div className="home-section-heading">
          <Title level={2} id={`${kind}-stage-title`}>
            当前阶段说明
          </Title>
          <Text type="secondary">本页是工作台主链路入口，不是完整业务实现。</Text>
        </div>
        <Card className="route-page-card" variant="outlined">
          <Space direction="vertical" size={12}>
            <Alert message={page.stage} type="info" showIcon />
            <Empty description={page.emptyTitle} />
            <Paragraph className="header-copy">{page.emptyDescription}</Paragraph>
            <List<string>
              size="small"
              dataSource={[...page.facts]}
              renderItem={(item) => (
                <List.Item>
                  <Text>{item}</Text>
                </List.Item>
              )}
            />
          </Space>
        </Card>
      </section>
    </main>
  );
}

function InterviewHistoryPage({ ownerId }: { ownerId: string }) {
  const [historyLoadState, setHistoryLoadState] = useState<HistoryLoadState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setHistoryLoadState({ status: "loading" });

    fetchInterviewHistory({ ownerId, signal: controller.signal })
      .then((response) => setHistoryLoadState({ status: "ready", response }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) {
          return;
        }
        const message = error instanceof Error ? error.message : "history request failed";
        setHistoryLoadState({ status: "failed", message });
      });

    return () => controller.abort();
  }, [ownerId]);

  const historyViewModel = useMemo(
    () =>
      buildHistoryViewModel(
        historyLoadState.status === "ready" ? historyLoadState.response : { items: [] },
        ownerId,
      ),
    [historyLoadState, ownerId],
  );

  return (
    <main className="app-shell workbench-route-shell">
      <WorkbenchNav />
      <section className="workspace-header" aria-labelledby="interviews-title">
        <div>
          <Text className="eyebrow">R1B-01 工作台入口 / 历史</Text>
          <Title level={1} id="interviews-title">
            历史记录
          </Title>
          <Paragraph className="header-copy">
            当前页面复用现有 `/api/v1/interviews` history contract，展示可进入可信详情页的最小列表。
          </Paragraph>
        </div>
        <div className="status-group" aria-label="历史记录当前阶段">
          <Tag color="blue">R1B-01</Tag>
          <Tag color="success">history contract</Tag>
        </div>
      </section>

      <section className="home-section" aria-labelledby="interviews-list-title">
        <div className="home-section-heading">
          <Title level={2} id="interviews-list-title">
            模拟面试历史列表
          </Title>
          <Text type="secondary">不新增后端 API；读取失败时保留稳定提示。</Text>
        </div>
        {historyLoadState.status === "loading" ? (
          <Alert className="trusted-alert" message="正在读取历史记录..." type="info" showIcon />
        ) : null}
        {historyLoadState.status === "failed" ? (
          <Alert
            className="trusted-alert"
            message="历史记录读取失败"
            description={historyLoadState.message}
            type="warning"
            showIcon
          />
        ) : null}
        <List
          className="home-record-list"
          dataSource={historyViewModel.items}
          locale={{ emptyText: <Empty description="暂无历史记录，入口已就绪。" /> }}
          renderItem={(record) => (
            <List.Item
              actions={[
                <a href={record.href} key="detail">
                  查看可信详情
                </a>,
              ]}
            >
              <List.Item.Meta
                title={
                  <div className="home-card-title-row">
                    <Text strong>{record.title}</Text>
                    <Tag color="processing">{record.status}</Tag>
                    <Tag color="geekblue">trace_summary: {record.traceStatus}</Tag>
                  </div>
                }
                description={
                  <div className="home-record-detail">
                    <Text>{record.traceCountLabel}</Text>
                    <div className="trusted-tag-row">
                      <Tag color={statusColor(record.reviewStatus)}>{record.scoreLabel}</Tag>
                      <Tag color={statusColor(record.reviewStatus)}>review: {record.reviewStatus}</Tag>
                      <Tag color={statusColor(record.exportStatus)}>export: {record.exportStatus}</Tag>
                      {record.exportRetryable ? <Tag color="warning">可重试</Tag> : null}
                    </div>
                    {record.exportFailureReason ? (
                      <Text type="danger">{record.exportFailureReason}</Text>
                    ) : null}
                    <TagList items={record.exportMetadata} emptyLabel="暂无 export snapshot / version" />
                    <Text type="secondary">
                      session: {record.sessionId} / owner: {record.ownerId} / mode: {record.mode} /
                      updated: {record.updatedAt}
                    </Text>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </section>
    </main>
  );
}

function ReviewListPage({ ownerId }: { ownerId: string }) {
  const [historyLoadState, setHistoryLoadState] = useState<HistoryLoadState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setHistoryLoadState({ status: "loading" });

    fetchInterviewHistory({ ownerId, signal: controller.signal })
      .then((response) => setHistoryLoadState({ status: "ready", response }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) {
          return;
        }
        const message = error instanceof Error ? error.message : "history request failed";
        setHistoryLoadState({ status: "failed", message });
      });

    return () => controller.abort();
  }, [ownerId]);

  const historyViewModel = useMemo(
    () =>
      buildHistoryViewModel(
        historyLoadState.status === "ready" ? historyLoadState.response : { items: [] },
        ownerId,
      ),
    [historyLoadState, ownerId],
  );

  return (
    <main className="app-shell workbench-route-shell">
      <WorkbenchNav />
      <section className="workspace-header" aria-labelledby="reviews-title">
        <div>
          <Text className="eyebrow">R1B-01 工作台入口 / 复盘</Text>
          <Title level={1} id="reviews-title">
            复盘
          </Title>
          <Paragraph className="header-copy">
            复用历史记录 contract 展示最近复盘入口、评分摘要、导出状态和降级提示。
          </Paragraph>
        </div>
        <div className="status-group" aria-label="复盘当前阶段">
          <Tag color="blue">R1 history</Tag>
          <Tag color="success">review/export summary</Tag>
        </div>
      </section>

      <section className="home-section" aria-labelledby="review-entry-title">
        <div className="home-section-heading">
          <Title level={2} id="review-entry-title">
            最近复盘入口
          </Title>
          <Text type="secondary">不新增复盘 API；从可信详情页继续查看完整证据链。</Text>
        </div>
        {historyLoadState.status === "loading" ? (
          <Alert className="trusted-alert" message="正在读取复盘摘要..." type="info" showIcon />
        ) : null}
        {historyLoadState.status === "failed" ? (
          <Alert
            className="trusted-alert"
            message="复盘摘要读取失败"
            description={historyLoadState.message}
            type="warning"
            showIcon
          />
        ) : null}
        <List
          className="home-record-list"
          dataSource={historyViewModel.items}
          locale={{ emptyText: <Empty description="暂无复盘记录，入口已就绪。" /> }}
          renderItem={(record) => (
            <List.Item
              actions={[
                <Button href={record.href} key="review-detail" type="link">
                  查看复盘详情
                </Button>,
              ]}
            >
              <List.Item.Meta
                title={
                  <div className="home-card-title-row">
                    <Text strong>{record.title}</Text>
                    <Tag color={statusColor(record.reviewStatus)}>review: {record.reviewStatus}</Tag>
                    <Tag color={statusColor(record.exportStatus)}>export: {record.exportStatus}</Tag>
                  </div>
                }
                description={
                  <div className="home-record-detail">
                    <div className="trusted-tag-row">
                      <Tag color="blue">{record.scoreLabel}</Tag>
                      <Tag color={statusColor(record.traceStatus)}>trace_summary: {record.traceStatus}</Tag>
                      {record.exportRetryable ? <Tag color="warning">可重试</Tag> : null}
                    </div>
                    {record.exportFailureReason ? (
                      <Text type="danger">{record.exportFailureReason}</Text>
                    ) : null}
                    <Text type="secondary">
                      session: {record.sessionId} / updated: {record.updatedAt}
                    </Text>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </section>
    </main>
  );
}

function TagList({ items, emptyLabel }: { items: string[]; emptyLabel: string }) {
  if (items.length === 0) {
    return <Text type="secondary">{emptyLabel}</Text>;
  }
  return (
    <div className="trusted-tag-row">
      {items.map((item) => (
        <Tag color="geekblue" key={item}>
          {item}
        </Tag>
      ))}
    </div>
  );
}

function statusColor(status: string): string {
  if (status === "failed") {
    return "error";
  }
  if (status === "degraded" || status === "retryable" || status === "pending") {
    return "warning";
  }
  if (status === "generated" || status === "completed" || status === "available") {
    return "success";
  }
  return "default";
}
