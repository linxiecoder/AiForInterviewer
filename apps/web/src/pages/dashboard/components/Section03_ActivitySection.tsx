import { Button, Card, List, Space, Tag, Typography } from "antd";
import { DASHBOARD_PAGE_COPY } from "../model/dashboardCopy";
import { ACTIVITY_ITEMS, type ActivityItem } from "../model/dashboardPlaceholderData";

import styles from "./sectionStyles.module.css";

type Section03ActivitySectionProps = {
  activityItems?: ActivityItem[];
};

export function Section03ActivitySection({
  activityItems = ACTIVITY_ITEMS,
}: Section03ActivitySectionProps) {
  const activityTagColor = {
    default: "blue",
    processing: "processing",
    success: "green",
    warning: "warning",
    error: "red",
  } as const;

  return (
    <Card
      className={styles.sectionCard}
      size="small"
      title={
        <div className={styles.activityHeader}>
          <Typography.Text strong>{DASHBOARD_PAGE_COPY.sections.activity.cardTitle}</Typography.Text>
          <Button type="link" disabled size="small">
            {DASHBOARD_PAGE_COPY.sections.activity.headerActionDisabledHint}
          </Button>
        </div>
      }
    >
      <List
        itemLayout="horizontal"
        dataSource={activityItems}
        split
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta
              title={
                <Space align="center" size={8}>
                  <Typography.Text strong>{item.title}</Typography.Text>
                  <Tag color={activityTagColor[item.status.tone]}>{item.status.label}</Tag>
                </Space>
              }
              description={
                <Space direction="vertical" size={2}>
                  <Typography.Text type="secondary">{item.description}</Typography.Text>
                  <Typography.Text type="secondary">{item.time}</Typography.Text>
                </Space>
              }
            />
          </List.Item>
        )}
      />

      <Typography.Text type="secondary" style={{ display: "block" }}>
        {DASHBOARD_PAGE_COPY.sections.activity.footer}
      </Typography.Text>
    </Card>
  );
}
