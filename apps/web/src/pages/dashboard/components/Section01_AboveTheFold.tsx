import { Card, Col, Row, Space, Tag, Typography } from "antd";
import { FileTextOutlined, AimOutlined, CarryOutOutlined, MessageOutlined } from "@ant-design/icons";
import { DASHBOARD_PAGE_COPY } from "../model/dashboardCopy";
import { OVERVIEW_METRICS, type OverviewMetric } from "../model/dashboardPlaceholderData";

import styles from "./sectionStyles.module.css";

type Section01AboveTheFoldProps = {
  items?: OverviewMetric[];
};

function resolveIcon(key: string) {
  if (key === "resume") {
    return <FileTextOutlined />;
  }
  if (key === "jobs") {
    return <AimOutlined />;
  }
  if (key === "progress") {
    return <CarryOutOutlined />;
  }
  return <MessageOutlined />;
}

export function Section01AboveTheFold({ items = OVERVIEW_METRICS }: Section01AboveTheFoldProps) {
  return (
    <Card
      className={styles.sectionCard}
      size="small"
      title={
        <Typography.Text strong>
          {DASHBOARD_PAGE_COPY.sections.above.cardsTitle}
        </Typography.Text>
      }
    >
      <Row gutter={[12, 12]}>
        {items.map((item) => (
          <Col key={item.key} xs={24} sm={12} lg={6}>
            <Card className={styles.metricCard} bordered={false}>
              <Space direction="vertical" size={10} className={styles.metricInner}>
                <Space align="center" className={styles.metricHeader}>
                  <span className={styles.metricIcon}>{resolveIcon(item.key)}</span>
                  <Typography.Text>{item.title}</Typography.Text>
                  <Tag color="blue" style={{ marginLeft: "auto" }}>
                    {item.trend}
                  </Tag>
                </Space>

                <Typography.Title level={3} className={styles.metricValue}>
                  {item.value}
                </Typography.Title>
                <Typography.Text type="secondary">{item.hint}</Typography.Text>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>
    </Card>
  );
}
