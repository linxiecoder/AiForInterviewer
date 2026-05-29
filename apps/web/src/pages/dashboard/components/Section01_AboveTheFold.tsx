import { Card, Col, Row, Space, Tag, Typography } from "antd";
import { FileTextOutlined, AimOutlined, CarryOutOutlined, MessageOutlined } from "@ant-design/icons";
import { DASHBOARD_PAGE_COPY } from "../model/dashboardCopy";
import type { DashboardOverviewMetric } from "../model/dashboardData";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { ErrorState } from "../../../shared/ui/ErrorState";
import { LoadingState } from "../../../shared/ui/LoadingState";

import styles from "./sectionStyles.module.css";

type Section01AboveTheFoldProps = {
  items: DashboardOverviewMetric[];
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  onRetry?: () => void;
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

export function Section01AboveTheFold({
  items,
  loading = false,
  error = null,
  empty = false,
  onRetry,
}: Section01AboveTheFoldProps) {
  if (loading) {
    return (
      <Card className={styles.sectionCard} size="small" title={DASHBOARD_PAGE_COPY.sections.above.cardsTitle}>
        <LoadingState compact message="加载首页指标" />
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={styles.sectionCard} size="small" title={DASHBOARD_PAGE_COPY.sections.above.cardsTitle}>
        <ErrorState compact message="首页指标加载失败" details={error} actionLabel="重试" onAction={onRetry} />
      </Card>
    );
  }

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
                    {item.sourceLabel}
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
      {empty ? <EmptyState compact description="暂无业务记录，指标按真实数据展示为 0。" /> : null}
    </Card>
  );
}
