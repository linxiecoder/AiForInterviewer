import { ArrowRightOutlined } from "@ant-design/icons";
import { Badge, Button, Tag, Typography } from "antd";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { ErrorState } from "../../../shared/ui/ErrorState";
import { LoadingState } from "../../../shared/ui/LoadingState";
import type { DashboardPriorityItem, DashboardPriorityTone, DashboardRouteTarget } from "../model/dashboardData";

import styles from "./sectionStyles.module.css";

type DashboardPriorityQueueProps = {
  items: DashboardPriorityItem[];
  loading?: boolean;
  error?: string | null;
  searchText: string;
  activePriority: DashboardPriorityTone | "all";
  onPriorityChange: (priority: DashboardPriorityTone | "all") => void;
  onRetry?: () => void;
  onOpenRoute: (href: DashboardRouteTarget) => void;
};

const PRIORITY_META: Record<DashboardPriorityTone, { label: string; className: string }> = {
  urgent: { label: "紧急", className: styles.toneError },
  important: { label: "重要", className: styles.toneWarning },
  normal: { label: "普通", className: styles.toneInfo },
};

const PRIORITY_FILTERS: Array<{ key: DashboardPriorityTone | "all"; label: string }> = [
  { key: "all", label: "全部" },
  { key: "urgent", label: "紧急" },
  { key: "important", label: "重要" },
  { key: "normal", label: "普通" },
];

function matchesSearch(item: DashboardPriorityItem, searchText: string): boolean {
  const keyword = searchText.trim().toLowerCase();
  if (!keyword) {
    return true;
  }
  return [item.title, item.description, item.actionLabel, item.sourceLabel]
    .join(" ")
    .toLowerCase()
    .includes(keyword);
}

export function DashboardPriorityQueue({
  items,
  loading = false,
  error = null,
  searchText,
  activePriority,
  onPriorityChange,
  onRetry,
  onOpenRoute,
}: DashboardPriorityQueueProps) {
  const visibleItems = items.filter((item) => {
    const priorityMatched = activePriority === "all" || item.priority === activePriority;
    return priorityMatched && matchesSearch(item, searchText);
  });
  const totalCount = items.reduce((sum, item) => sum + item.count, 0);

  return (
    <section className={styles.panel} aria-labelledby="dashboard-priority-title">
      <div className={styles.panelHeader}>
        <div>
          <Typography.Title level={2} id="dashboard-priority-title" className={styles.panelTitle}>
            今日优先队列
          </Typography.Title>
          <Typography.Text type="secondary" className={styles.panelHint}>
            {totalCount > 0 ? `共 ${totalCount} 项，按影响今天准备闭环排序。` : "暂无待办事项。"}
          </Typography.Text>
        </div>
      </div>

      <div className={styles.filterBar} role="group" aria-label="优先级筛选">
        {PRIORITY_FILTERS.map((filter) => (
          <button
            key={filter.key}
            type="button"
            className={filter.key === activePriority ? styles.filterChipActive : styles.filterChip}
            onClick={() => onPriorityChange(filter.key)}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {loading ? <LoadingState compact message="加载今日优先队列" /> : null}
      {!loading && error ? <ErrorState compact message="今日优先队列加载失败" details={error} actionLabel="重试" onAction={onRetry} /> : null}
      {!loading && !error && visibleItems.length === 0 ? (
        <EmptyState compact description={searchText || activePriority !== "all" ? "当前筛选下暂无任务。" : "暂无今日优先任务。"} />
      ) : null}
      {!loading && !error && visibleItems.length > 0 ? (
        <div className={styles.queueList}>
          {visibleItems.map((item) => (
            <button
              key={item.key}
              type="button"
              className={styles.queueRow}
              onClick={() => onOpenRoute(item.href)}
            >
              <span className={styles.queuePriority}>
                <Tag className={`${styles.statusTag} ${PRIORITY_META[item.priority].className}`}>
                  {PRIORITY_META[item.priority].label}
                </Tag>
                <Badge count={item.count} />
              </span>
              <span className={styles.queueMain}>
                <span className={styles.queueTitle}>{item.title}</span>
                <span className={styles.queueDescription}>{item.description}</span>
              </span>
              <span className={styles.queueAction}>
                {item.actionLabel}
                <ArrowRightOutlined aria-hidden />
              </span>
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
