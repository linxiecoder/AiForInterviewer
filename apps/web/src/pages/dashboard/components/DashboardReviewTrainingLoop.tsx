import { ArrowRightOutlined } from "@ant-design/icons";
import { Tag, Typography } from "antd";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { ErrorState } from "../../../shared/ui/ErrorState";
import { LoadingState } from "../../../shared/ui/LoadingState";
import type { DashboardReviewTrainingLoopStage, DashboardRouteTarget, DashboardSignalTone } from "../model/dashboardData";

import styles from "./sectionStyles.module.css";

type DashboardReviewTrainingLoopProps = {
  stages: DashboardReviewTrainingLoopStage[];
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

export function DashboardReviewTrainingLoop({
  stages,
  loading = false,
  error = null,
  onRetry,
  onOpenRoute,
}: DashboardReviewTrainingLoopProps) {
  return (
    <section className={styles.panel} aria-labelledby="dashboard-review-loop-title">
      <div className={styles.panelHeader}>
        <div>
          <Typography.Title level={2} id="dashboard-review-loop-title" className={styles.panelTitle}>
            复盘训练闭环
          </Typography.Title>
          <Typography.Text type="secondary" className={styles.panelHint}>
            模拟面试、报告、薄弱项、训练建议和资产沉淀都来自现有数据。
          </Typography.Text>
        </div>
      </div>

      {loading ? <LoadingState compact message="加载复盘训练闭环" /> : null}
      {!loading && error ? <ErrorState compact message="复盘训练闭环加载失败" details={error} actionLabel="重试" onAction={onRetry} /> : null}
      {!loading && !error && stages.length === 0 ? <EmptyState compact description="暂无复盘训练闭环数据" /> : null}
      {!loading && !error && stages.length > 0 ? (
        <div className={styles.loopRail}>
          {stages.map((stage, index) => (
            <button
              key={stage.key}
              type="button"
              className={styles.loopStage}
              onClick={() => onOpenRoute(stage.href)}
              aria-label={`${stage.title}：${stage.statusLabel}，${stage.description}`}
            >
              <span className={styles.loopIndex}>{index + 1}</span>
              <span className={styles.loopText}>
                <strong>{stage.title}</strong>
                <span>{stage.description}</span>
              </span>
              <Tag className={`${styles.statusTag} ${TONE_CLASS[stage.tone]}`}>{stage.statusLabel}</Tag>
              {index < stages.length - 1 ? <ArrowRightOutlined className={styles.loopArrow} aria-hidden /> : null}
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
