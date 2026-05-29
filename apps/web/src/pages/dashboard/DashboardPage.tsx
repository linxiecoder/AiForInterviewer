import { Space, Typography } from "antd";
import { AppShell } from "../../widgets/app-shell/AppShell";
import {
  DashboardFrame,
  Section01AboveTheFold,
  Section02TodoSection,
  Section03ActivitySection,
} from "./components";
import { DASHBOARD_PAGE_COPY } from "./model/dashboardCopy";
import { DASHBOARD_SECTION_STATE_BY_FRAME, readDashboardFrameMode } from "./model/dashboardSections";
import { useDashboardData } from "./model/useDashboardData";
import type { DashboardRouteTarget } from "./model/dashboardData";
import { useRouteController } from "../../app/routes/router";

import styles from "./DashboardPage.module.css";

export function DashboardPage() {
  const { navigate } = useRouteController();
  const frameMode = readDashboardFrameMode();
  const sectionStates = DASHBOARD_SECTION_STATE_BY_FRAME[frameMode];
  const dashboardState = useDashboardData();

  const loading = dashboardState.status === "loading";
  const error = dashboardState.status === "error" ? dashboardState.error : null;
  const data = dashboardState.status === "ready" ? dashboardState.data : null;

  const openTodo = (href: DashboardRouteTarget) => {
    navigate(href);
  };

  return (
    <AppShell>
      <div className={styles.dashboardPage}>
        <div>
          <Typography.Title level={4} className={styles.pageTitle}>
            {DASHBOARD_PAGE_COPY.pageTitle}
          </Typography.Title>
          <Typography.Text type="secondary">{DASHBOARD_PAGE_COPY.frameHint}</Typography.Text>
        </div>

        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <DashboardFrame
            title="Section01_AboveTheFold"
            state={sectionStates.above}
            frameMode={frameMode}
            disabledReason={DASHBOARD_PAGE_COPY.sections.above.disabledActionHint}
          >
            <Section01AboveTheFold
              items={data?.overviewMetrics ?? []}
              loading={loading}
              error={error}
              empty={data?.isSourceEmpty ?? false}
              onRetry={dashboardState.reload}
            />
          </DashboardFrame>

          <DashboardFrame
            title="Section02_TodoSection"
            state={sectionStates.todo}
            frameMode={frameMode}
            disabledReason={DASHBOARD_PAGE_COPY.sections.todo.disabledActionHint}
          >
            <Section02TodoSection
              todoItems={data?.todoItems ?? []}
              loading={loading}
              error={error}
              onRetry={dashboardState.reload}
              onOpenTodo={openTodo}
            />
          </DashboardFrame>

          <DashboardFrame
            title="Section03_ActivitySection"
            state={sectionStates.activity}
            frameMode={frameMode}
            disabledReason={DASHBOARD_PAGE_COPY.sections.activity.headerActionDisabledHint}
          >
            <Section03ActivitySection
              activityItems={data?.activityItems ?? []}
              loading={loading}
              error={error}
              onRetry={dashboardState.reload}
            />
          </DashboardFrame>
        </Space>
      </div>
    </AppShell>
  );
}
