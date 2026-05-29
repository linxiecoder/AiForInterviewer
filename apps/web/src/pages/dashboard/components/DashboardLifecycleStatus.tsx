import { ArrowRightOutlined } from "@ant-design/icons";
import { Button, Progress, Tag, Typography } from "antd";
import { useState } from "react";
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
const LIFECYCLE_PAGE_SIZE = 2;

export function DashboardLifecycleStatus({
  steps,
  loading = false,
  error = null,
  onRetry,
  onOpenRoute,
}: DashboardLifecycleStatusProps) {
  const [pageIndex, setPageIndex] = useState(0);
  const pageCount = Math.max(1, Math.ceil(steps.length / LIFECYCLE_PAGE_SIZE));
  const currentPageIndex = Math.min(pageIndex, pageCount - 1);
  const pageSteps = steps.slice(
    currentPageIndex * LIFECYCLE_PAGE_SIZE,
    currentPageIndex * LIFECYCLE_PAGE_SIZE + LIFECYCLE_PAGE_SIZE,
  );

  return (
    <section className={styles.panel} aria-labelledby="dashboard-lifecycle-title">
      <div className={styles.panelHeader}>
        <div>
          <Typography.Title level={2} id="dashboard-lifecycle-title" className={styles.panelTitle}>
            准备链路状态
          </Typography.Title>
        </div>
      </div>

      <div className={steps.length === 0 ? `${styles.panelBody} ${styles.panelBodyCenter}` : styles.panelBody}>
        {loading ? <LoadingState compact message="加载准备链路" /> : null}
        {!loading && error ? <ErrorState compact message="准备链路加载失败" details={error} actionLabel="重试" onAction={onRetry} /> : null}
        {!loading && !error && steps.length === 0 ? <EmptyState compact description="暂无准备链路数据" /> : null}
        {!loading && !error && steps.length > 0 ? (
          <>
            <div className={styles.lifecycleList}>
              {pageSteps.map((step, index) => (
                <button
                  key={step.key}
                  type="button"
                  className={styles.lifecycleStep}
                  onClick={() => onOpenRoute(step.href)}
                  aria-label={`${step.title}：${step.statusLabel}，${step.description}`}
                >
                  <span className={styles.stepIndex}>{currentPageIndex * LIFECYCLE_PAGE_SIZE + index + 1}</span>
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
            {steps.length > LIFECYCLE_PAGE_SIZE ? (
              <div className={styles.panelPager} aria-label="准备链路状态分页">
                <Button size="small" disabled={currentPageIndex === 0} onClick={() => setPageIndex(currentPageIndex - 1)}>
                  上一页
                </Button>
                <span>{currentPageIndex + 1} / {pageCount}</span>
                <Button size="small" disabled={currentPageIndex >= pageCount - 1} onClick={() => setPageIndex(currentPageIndex + 1)}>
                  下一页
                </Button>
              </div>
            ) : null}
          </>
        ) : null}
      </div>
    </section>
  );
}
