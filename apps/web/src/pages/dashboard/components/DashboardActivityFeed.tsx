import { Tag, Typography } from "antd";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { ErrorState } from "../../../shared/ui/ErrorState";
import { LoadingState } from "../../../shared/ui/LoadingState";
import type { DashboardActivityItem, DashboardActivitySourceKey, DashboardSignalTone } from "../model/dashboardData";

import styles from "./sectionStyles.module.css";

type DashboardActivityFeedProps = {
  activityItems: DashboardActivityItem[];
  loading?: boolean;
  error?: string | null;
  searchText: string;
  onRetry?: () => void;
};

const SOURCE_LABEL: Record<DashboardActivitySourceKey, string> = {
  resume: "简历",
  job: "岗位",
  polish_session: "模拟面试",
  asset: "资产",
  weakness: "薄弱项",
};

const TONE_CLASS: Record<DashboardSignalTone, string> = {
  default: styles.toneDefault,
  processing: styles.toneInfo,
  success: styles.toneSuccess,
  warning: styles.toneWarning,
  error: styles.toneError,
};

function matchesSearch(item: DashboardActivityItem, searchText: string): boolean {
  const keyword = searchText.trim().toLowerCase();
  if (!keyword) {
    return true;
  }
  return [SOURCE_LABEL[item.source], item.title, item.status.label, item.description, item.time]
    .join(" ")
    .toLowerCase()
    .includes(keyword);
}

export function DashboardActivityFeed({
  activityItems,
  loading = false,
  error = null,
  searchText,
  onRetry,
}: DashboardActivityFeedProps) {
  const visibleItems = activityItems.filter((item) => matchesSearch(item, searchText));

  return (
    <section className={styles.panel} aria-labelledby="dashboard-activity-title">
      <div className={styles.panelHeader}>
        <div>
          <Typography.Title level={2} id="dashboard-activity-title" className={styles.panelTitle}>
            最近活动
          </Typography.Title>
          <Typography.Text type="secondary" className={styles.panelHint}>
            最近 8 条真实业务记录，按更新时间排序。
          </Typography.Text>
        </div>
      </div>

      {loading ? <LoadingState compact message="加载最近活动" /> : null}
      {!loading && error ? <ErrorState compact message="最近活动加载失败" details={error} actionLabel="重试" onAction={onRetry} /> : null}
      {!loading && !error && visibleItems.length === 0 ? (
        <EmptyState compact description={searchText ? "当前搜索下暂无最近活动。" : "暂无最近活动。"} />
      ) : null}
      {!loading && !error && visibleItems.length > 0 ? (
        <div className={styles.activityTable} role="list" aria-label="最近活动列表">
          {visibleItems.map((item) => (
            <div key={item.key} className={styles.activityRow} role="listitem">
              <span className={styles.activitySource}>{SOURCE_LABEL[item.source]}</span>
              <span className={styles.activityMain}>
                <strong>{item.title}</strong>
                <span>{item.description}</span>
              </span>
              <Tag className={`${styles.statusTag} ${TONE_CLASS[item.status.tone]}`}>{item.status.label}</Tag>
              <span className={styles.activityTime}>{item.time}</span>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
