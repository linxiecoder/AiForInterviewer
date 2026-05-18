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

import styles from "./DashboardPage.module.css";

export function DashboardPage() {
  const frameMode = readDashboardFrameMode();
  const sectionStates = DASHBOARD_SECTION_STATE_BY_FRAME[frameMode];

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
            <Section01AboveTheFold />
          </DashboardFrame>

          <DashboardFrame
            title="Section02_TodoSection"
            state={sectionStates.todo}
            frameMode={frameMode}
            disabledReason={DASHBOARD_PAGE_COPY.sections.todo.disabledActionHint}
          >
            <Section02TodoSection />
          </DashboardFrame>

          <DashboardFrame
            title="Section03_ActivitySection"
            state={sectionStates.activity}
            frameMode={frameMode}
            disabledReason={DASHBOARD_PAGE_COPY.sections.activity.headerActionDisabledHint}
          >
            <Section03ActivitySection />
          </DashboardFrame>
        </Space>
      </div>
    </AppShell>
  );
}
