import { ArrowRightOutlined } from "@ant-design/icons";
import { Progress, Tag, Typography } from "antd";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { ErrorState } from "../../../shared/ui/ErrorState";
import { LoadingState } from "../../../shared/ui/LoadingState";
import type { DashboardLifecycleStep, DashboardRouteTarget, DashboardSignalTone } from "../model/dashboardData";

import styles from "./sectionStyles.module.css";

type DashboardLifecycleStatusProps = {
  steps: DashboardLifecycleStep[];
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  onOpenRoute: (href: DashboardRouteTarget) => void;
};

const TONE_CLASS: Record<DashboardSignalTone, string> = {
  default: styles.toneDefault,
  processing: styles.toneInfo,
  success: styles.toneSuccess,
  warning: styles.toneWarning,
  error: styles.toneError,
};

export function DashboardLifecycleStatus({
  steps,
  loading = false,
  error = null,
  onRetry,
  onOpenRoute,
}: DashboardLifecycleStatusProps) {
  return (
    <section className={styles.panel} aria-labelledby="dashboard-lifecycle-title">
      <div className={styles.panelHeader}>
        <div>
          <Typography.Title level={2} id="dashboard-lifecycle-title" className={styles.panelTitle}>
            准备链路状态
          </Typography.Title>
          <Typography.Text type="secondary" className={styles.panelHint}>
            缺少数据的阶段显示 0 或待配置，不补造进度。
          </Typography.Text>
        </div>
      </div>

      {loading ? <LoadingState compact message="加载准备链路" /> : null}
      {!loading && error ? <ErrorState compact message="准备链路加载失败" details={error} actionLabel="重试" onAction={onRetry} /> : null}
      {!loading && !error && steps.length === 0 ? <EmptyState compact description="暂无准备链路数据" /> : null}
      {!loading && !error && steps.length > 0 ? (
        <div className={styles.lifecycleList}>
          {steps.map((step, index) => (
            <button
              key={step.key}
              type="button"
              className={styles.lifecycleStep}
              onClick={() => onOpenRoute(step.href)}
              aria-label={`${step.title}：${step.statusLabel}，${step.description}`}
            >
              <span className={styles.stepIndex}>{index + 1}</span>
              <span className={styles.stepContent}>
                <span className={styles.stepTitleRow}>
                  <strong>{step.title}</strong>
                  <Tag className={`${styles.statusTag} ${TONE_CLASS[step.tone]}`}>{step.statusLabel}</Tag>
                </span>
                <Progress percent={step.progressPercent} size="small" showInfo={false} />
                <span className={styles.stepDescription}>{step.description}</span>
              </span>
              <ArrowRightOutlined className={styles.stepArrow} aria-hidden />
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
