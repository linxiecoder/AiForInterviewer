import { ArrowRightOutlined } from "@ant-design/icons";
import { Button, Typography } from "antd";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { ErrorState } from "../../../shared/ui/ErrorState";
import { LoadingState } from "../../../shared/ui/LoadingState";
import type { DashboardQuickAction, DashboardRouteTarget } from "../model/dashboardData";

import styles from "./sectionStyles.module.css";

type DashboardQuickActionsProps = {
  actions: DashboardQuickAction[];
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  onOpenRoute: (href: DashboardRouteTarget) => void;
};

export function DashboardQuickActions({
  actions,
  loading = false,
  error = null,
  onRetry,
  onOpenRoute,
}: DashboardQuickActionsProps) {
  return (
    <section className={styles.panel} aria-labelledby="dashboard-quick-actions-title">
      <div className={styles.panelHeader}>
        <div>
          <Typography.Title level={2} id="dashboard-quick-actions-title" className={styles.panelTitle}>
            快捷入口
          </Typography.Title>
          <Typography.Text type="secondary" className={styles.panelHint}>
            只跳转到已存在的业务路由。
          </Typography.Text>
        </div>
      </div>

      {loading ? <LoadingState compact message="加载快捷入口" /> : null}
      {!loading && error ? <ErrorState compact message="快捷入口加载失败" details={error} actionLabel="重试" onAction={onRetry} /> : null}
      {!loading && !error && actions.length === 0 ? <EmptyState compact description="暂无快捷入口" /> : null}
      {!loading && !error && actions.length > 0 ? (
        <div className={styles.quickGrid}>
          {actions.map((action) => (
            <div key={action.key} className={styles.quickAction}>
              <div className={styles.quickActionText}>
                <strong>{action.title}</strong>
                <span>{action.description}</span>
                {action.disabledReason ? <small>{action.disabledReason}</small> : null}
              </div>
              <Button
                type={action.primary ? "primary" : "default"}
                size="small"
                disabled={Boolean(action.disabledReason)}
                title={action.disabledReason}
                icon={<ArrowRightOutlined />}
                iconPosition="end"
                onClick={() => onOpenRoute(action.href)}
              >
                {action.actionLabel}
              </Button>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
