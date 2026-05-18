import { Alert, Button, Card, List, Typography } from "antd";
import { DASHBOARD_PAGE_COPY } from "../model/dashboardCopy";
import { EMPTY_STATE_SECTIONS } from "../model/dashboardPlaceholderData";

type Section04EmptyStatesProps = {
  sections?: string[];
};

export function Section04EmptyStates({ sections = EMPTY_STATE_SECTIONS }: Section04EmptyStatesProps) {
  return (
    <Card size="small" title={DASHBOARD_PAGE_COPY.sections.empty.title}>
      <Typography.Text type="secondary" style={{ display: "block", marginBottom: 8 }}>
        {DASHBOARD_PAGE_COPY.sections.empty.sectionHeader}
      </Typography.Text>
      <Typography.Text type="secondary" style={{ display: "block", marginBottom: 12 }}>
        {DASHBOARD_PAGE_COPY.sections.empty.description}
      </Typography.Text>
      <Alert
        type="warning"
        showIcon
        message={DASHBOARD_PAGE_COPY.emptyStates.guidanceTitle}
        description={DASHBOARD_PAGE_COPY.emptyStates.guidanceDescription}
      />
      <List
        itemLayout="horizontal"
        dataSource={sections}
        style={{ marginTop: 12 }}
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta title={item} description={DASHBOARD_PAGE_COPY.emptyStates.todoHint} />
          </List.Item>
        )}
      />
      <div style={{ marginTop: 12 }}>
        <Button type="primary" disabled>
          {DASHBOARD_PAGE_COPY.emptyStates.createAction}
        </Button>
      </div>
      <Typography.Text type="secondary" style={{ display: "block", marginTop: 12 }}>
        {DASHBOARD_PAGE_COPY.sections.empty.footer}
      </Typography.Text>
    </Card>
  );
}
