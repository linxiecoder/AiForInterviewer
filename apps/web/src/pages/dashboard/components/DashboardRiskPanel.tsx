import { ArrowRightOutlined } from "@ant-design/icons";
import { Tag, Typography } from "antd";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { ErrorState } from "../../../shared/ui/ErrorState";
import { LoadingState } from "../../../shared/ui/LoadingState";
import type { DashboardRiskSignal, DashboardRouteTarget } from "../model/dashboardData";

import styles from "./sectionStyles.module.css";

type DashboardRiskPanelProps = {
  signals: DashboardRiskSignal[];
  loading?: boolean;
  error?: string | null;
  searchText: string;
  onRetry?: () => void;
  onOpenRoute: (href: DashboardRouteTarget) => void;
};

function matchesSearch(signal: DashboardRiskSignal, searchText: string): boolean {
  const keyword = searchText.trim().toLowerCase();
  if (!keyword) {
    return true;
  }
  return [signal.title, signal.description, signal.statusLabel, signal.sourceLabel, signal.actionLabel]
    .join(" ")
    .toLowerCase()
    .includes(keyword);
}

function resolveSeverityClass(severity: string): string {
  if (severity === "critical" || severity === "high") {
    return styles.toneError;
  }
  if (severity === "medium") {
    return styles.toneWarning;
  }
  return styles.toneInfo;
}

export function DashboardRiskPanel({
  signals,
  loading = false,
  error = null,
  searchText,
  onRetry,
  onOpenRoute,
}: DashboardRiskPanelProps) {
  const visibleSignals = signals.filter((signal) => matchesSearch(signal, searchText));

  return (
    <section className={styles.panel} aria-labelledby="dashboard-risk-title">
      <div className={styles.panelHeader}>
        <div>
          <Typography.Title level={2} id="dashboard-risk-title" className={styles.panelTitle}>
            风险与薄弱项
          </Typography.Title>
          <Typography.Text type="secondary" className={styles.panelHint}>
            只展示真实薄弱项、严重度和证据来源。
          </Typography.Text>
        </div>
      </div>

      {loading ? <LoadingState compact message="加载薄弱项" /> : null}
      {!loading && error ? <ErrorState compact message="薄弱项加载失败" details={error} actionLabel="重试" onAction={onRetry} /> : null}
      {!loading && !error && visibleSignals.length === 0 ? (
        <EmptyState compact description={searchText ? "当前搜索下暂无薄弱项。" : "暂无薄弱项。"} />
      ) : null}
      {!loading && !error && visibleSignals.length > 0 ? (
        <div className={styles.riskList}>
          {visibleSignals.map((signal) => (
            <button
              key={signal.key}
              type="button"
              className={styles.riskItem}
              onClick={() => onOpenRoute(signal.href)}
            >
              <span className={styles.riskItemHeader}>
                <strong>{signal.title}</strong>
                <Tag className={`${styles.statusTag} ${resolveSeverityClass(signal.severity)}`}>
                  {signal.statusLabel}
                </Tag>
              </span>
              <span className={styles.riskDescription}>{signal.description}</span>
              <span className={styles.riskFooter}>
                <span>{signal.sourceLabel}</span>
                <span className={styles.inlineAction}>
                  {signal.actionLabel}
                  <ArrowRightOutlined aria-hidden />
                </span>
              </span>
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
