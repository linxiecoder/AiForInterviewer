import { AimOutlined, FileTextOutlined, PlayCircleOutlined, SearchOutlined } from "@ant-design/icons";
import { Alert, Button, Input, Typography } from "antd";
import { useMemo, useState } from "react";
import { AppShell } from "../../widgets/app-shell/AppShell";
import {
  DashboardActivityFeed,
  DashboardKpiStrip,
  DashboardLifecycleStatus,
  DashboardPriorityQueue,
  DashboardQuickActions,
  DashboardReviewTrainingLoop,
  DashboardRiskPanel,
} from "./components";
import { DASHBOARD_PAGE_COPY } from "./model/dashboardCopy";
import { readDashboardFrameMode } from "./model/dashboardSections";
import { useDashboardData } from "./model/useDashboardData";
import { buildDashboardData, type DashboardPriorityTone, type DashboardQuickAction, type DashboardRouteTarget } from "./model/dashboardData";
import { useRouteController } from "../../app/routes/router";

import styles from "./DashboardPage.module.css";

const EMPTY_DASHBOARD_DATA = buildDashboardData({
  resumes: [],
  jobs: [],
  polishSessions: [],
  assets: [],
  weaknesses: [],
});

export function DashboardPage() {
  const { navigate } = useRouteController();
  const [searchText, setSearchText] = useState("");
  const [activePriority, setActivePriority] = useState<DashboardPriorityTone | "all">("all");
  const frameMode = readDashboardFrameMode();
  const dashboardState = useDashboardData();

  const loading = frameMode === "loading" || dashboardState.status === "loading";
  const error =
    frameMode === "error"
      ? "当前为 frame=error 调试状态，可点击重试重新读取真实业务数据。"
      : dashboardState.status === "error"
        ? dashboardState.error
        : null;
  const data = frameMode === "empty" || frameMode === "disabled"
    ? EMPTY_DASHBOARD_DATA
    : dashboardState.status === "ready"
      ? dashboardState.data
      : EMPTY_DASHBOARD_DATA;
  const pageDisabled = frameMode === "disabled";
  const isSourceEmpty = frameMode === "empty" || data.isSourceEmpty;

  const headerActions = useMemo(() => {
    const byKey = new Map(data.quickActions.map((action) => [action.key, action]));
    return {
      startInterview: byKey.get("start-interview"),
      newResume: byKey.get("new-resume"),
      newJob: byKey.get("new-job"),
    };
  }, [data.quickActions]);

  const openRoute = (href: DashboardRouteTarget) => {
    if (pageDisabled) {
      return;
    }
    navigate(href);
  };

  const runQuickAction = (action: DashboardQuickAction | undefined) => {
    if (!action || action.disabledReason || pageDisabled) {
      return;
    }
    openRoute(action.href);
  };

  return (
    <AppShell>
      <div className={styles.dashboardPage}>
        <header className={styles.workbenchHeader}>
          <div className={styles.titleBlock}>
            <Typography.Title level={1} className={styles.pageTitle}>
              {DASHBOARD_PAGE_COPY.pageTitle}
            </Typography.Title>
            <Typography.Text type="secondary" className={styles.pageSubtitle}>
              {DASHBOARD_PAGE_COPY.frameHint}
            </Typography.Text>
          </div>

          <Input
            className={styles.searchInput}
            allowClear
            prefix={<SearchOutlined aria-hidden />}
            placeholder={DASHBOARD_PAGE_COPY.searchPlaceholder}
            aria-label="搜索简历、岗位、模拟面试、薄弱项和资产"
            value={searchText}
            disabled={loading || pageDisabled}
            onChange={(event) => setSearchText(event.target.value)}
          />

          <div className={styles.headerActions}>
            <Button
              icon={<FileTextOutlined />}
              disabled={loading || pageDisabled}
              onClick={() => runQuickAction(headerActions.newResume)}
            >
              新增简历
            </Button>
            <Button
              icon={<AimOutlined />}
              disabled={loading || pageDisabled}
              onClick={() => runQuickAction(headerActions.newJob)}
            >
              新增岗位
            </Button>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              disabled={loading || pageDisabled || Boolean(headerActions.startInterview?.disabledReason)}
              title={headerActions.startInterview?.disabledReason}
              onClick={() => runQuickAction(headerActions.startInterview)}
            >
              发起模拟面试
            </Button>
          </div>
        </header>

        {pageDisabled ? (
          <Alert
            type="info"
            showIcon
            message="当前为 disabled 调试态"
            description="页面保留结构，但搜索、跳转和主操作均禁用。"
          />
        ) : null}

        {isSourceEmpty && !loading && !error ? (
          <Alert
            type="warning"
            showIcon
            message="暂无业务记录"
            description="当前首页所有数字均来自真实接口空结果，没有使用原型静态数据。"
          />
        ) : null}

        <DashboardKpiStrip
          items={data.overviewMetrics}
          loading={loading}
          error={error}
          empty={isSourceEmpty}
          onRetry={dashboardState.reload}
          onOpenRoute={openRoute}
        />

        <DashboardReviewTrainingLoop
          stages={data.reviewTrainingLoop}
          loading={loading}
          error={error}
          onRetry={dashboardState.reload}
          onOpenRoute={openRoute}
        />

        <div className={styles.primaryGrid}>
          <DashboardPriorityQueue
            items={data.priorityItems}
            loading={loading}
            error={error}
            searchText={searchText}
            activePriority={activePriority}
            onPriorityChange={setActivePriority}
            onRetry={dashboardState.reload}
            onOpenRoute={openRoute}
          />

          <DashboardLifecycleStatus
            steps={data.lifecycleSteps}
            loading={loading}
            error={error}
            onRetry={dashboardState.reload}
            onOpenRoute={openRoute}
          />

          <DashboardRiskPanel
            signals={data.riskSignals}
            loading={loading}
            error={error}
            searchText={searchText}
            onRetry={dashboardState.reload}
            onOpenRoute={openRoute}
          />
        </div>

        <div className={styles.secondaryGrid}>
          <DashboardActivityFeed
            activityItems={data.activityItems}
            loading={loading}
            error={error}
            searchText={searchText}
            onRetry={dashboardState.reload}
          />

          <DashboardQuickActions
            actions={data.quickActions}
            loading={loading}
            error={error}
            onRetry={dashboardState.reload}
            onOpenRoute={openRoute}
          />
        </div>
      </div>
    </AppShell>
  );
}
