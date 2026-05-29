import {
  AimOutlined,
  CarryOutOutlined,
  FileDoneOutlined,
  FileTextOutlined,
  MessageOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { Typography } from "antd";
import type { ReactNode } from "react";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { ErrorState } from "../../../shared/ui/ErrorState";
import { LoadingState } from "../../../shared/ui/LoadingState";
import type { DashboardMetricKey, DashboardOverviewMetric, DashboardRouteTarget } from "../model/dashboardData";

import styles from "./sectionStyles.module.css";

type DashboardKpiStripProps = {
  items: DashboardOverviewMetric[];
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  onRetry?: () => void;
  onOpenRoute: (href: DashboardRouteTarget) => void;
};

const KPI_META: Record<DashboardMetricKey, { icon: ReactNode; href: DashboardRouteTarget }> = {
  resume: { icon: <FileTextOutlined />, href: "/resume" },
  jobs: { icon: <AimOutlined />, href: "/job" },
  progress: { icon: <CarryOutOutlined />, href: "/job" },
  mock: { icon: <MessageOutlined />, href: "/interview" },
  asset: { icon: <FileDoneOutlined />, href: "/asset" },
  weakness: { icon: <WarningOutlined />, href: "/weakness" },
};

export function DashboardKpiStrip({
  items,
  loading = false,
  error = null,
  empty = false,
  onRetry,
  onOpenRoute,
}: DashboardKpiStripProps) {
  if (loading) {
    return (
      <section className={styles.panel} aria-label="首页关键指标">
        <LoadingState compact message="加载首页指标" />
      </section>
    );
  }

  if (error) {
    return (
      <section className={styles.panel} aria-label="首页关键指标">
        <ErrorState compact message="首页指标加载失败" details={error} actionLabel="重试" onAction={onRetry} />
      </section>
    );
  }

  return (
    <section className={styles.kpiStrip} aria-label="首页关键指标">
      {items.map((item) => (
        <button
          key={item.key}
          type="button"
          className={styles.kpiTile}
          onClick={() => onOpenRoute(KPI_META[item.key].href)}
          aria-label={`${item.title}：${item.value}`}
        >
          <span className={styles.kpiHeader}>
            <span className={styles.kpiIcon} aria-hidden>
              {KPI_META[item.key].icon}
            </span>
            <Typography.Text className={styles.kpiLabel}>{item.title}</Typography.Text>
          </span>
          <strong className={styles.kpiValue}>{item.value}</strong>
        </button>
      ))}
      {empty ? (
        <div className={styles.inlineEmpty}>
          <EmptyState compact description="暂无业务记录，指标按真实数据展示为 0。" />
        </div>
      ) : null}
    </section>
  );
}
