import { Card, List, Space, Tag, Typography } from "antd";
import { DASHBOARD_PAGE_COPY } from "../model/dashboardCopy";
import type { DashboardActivityItem } from "../model/dashboardData";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { ErrorState } from "../../../shared/ui/ErrorState";
import { LoadingState } from "../../../shared/ui/LoadingState";

import styles from "./sectionStyles.module.css";

type Section03ActivitySectionProps = {
  activityItems: DashboardActivityItem[];
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
};

export function Section03ActivitySection({
  activityItems,
  loading = false,
  error = null,
  onRetry,
}: Section03ActivitySectionProps) {
  const activityTagColor = {
    default: "blue",
    processing: "processing",
    success: "green",
    warning: "warning",
    error: "red",
  } as const;

  return (
    <Card
      className={styles.sectionCard}
      size="small"
      title={
        <div className={styles.activityHeader}>
          <Typography.Text strong>{DASHBOARD_PAGE_COPY.sections.activity.cardTitle}</Typography.Text>
        </div>
      }
    >
      {loading ? <LoadingState compact message="加载最近活动" /> : null}
      {!loading && error ? <ErrorState compact message="最近活动加载失败" details={error} actionLabel="重试" onAction={onRetry} /> : null}
      {!loading && !error && activityItems.length === 0 ? <EmptyState compact description="暂无最近活动" /> : null}
      {!loading && !error && activityItems.length > 0 ? (
      <List
        itemLayout="horizontal"
        dataSource={activityItems}
        split
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta
              title={
                <Space align="center" size={8}>
                  <Typography.Text strong>{item.title}</Typography.Text>
                  <Tag color={activityTagColor[item.status.tone]}>{item.status.label}</Tag>
                </Space>
              }
              description={
                <Space direction="vertical" size={2}>
                  <Typography.Text type="secondary">{item.description}</Typography.Text>
                  <Typography.Text type="secondary">{item.time}</Typography.Text>
                </Space>
              }
            />
          </List.Item>
        )}
      />
      ) : null}
    </Card>
  );
}
