import { AimOutlined, ArrowRightOutlined, ExclamationCircleOutlined, InfoCircleOutlined, WarningOutlined } from "@ant-design/icons";
import { Badge, Button, Card, Col, Row, Space, Tag, Typography } from "antd";
import type { KeyboardEvent, ReactNode } from "react";
import { DASHBOARD_PAGE_COPY } from "../model/dashboardCopy";
import type { DashboardRouteTarget, DashboardTodoItem } from "../model/dashboardData";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { ErrorState } from "../../../shared/ui/ErrorState";
import { LoadingState } from "../../../shared/ui/LoadingState";

import styles from "./sectionStyles.module.css";

type Section02TodoSectionProps = {
  todoItems: DashboardTodoItem[];
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  onOpenTodo: (href: DashboardRouteTarget) => void;
};

type PriorityVisual = {
  label: string;
  dotColor: string;
  icon: ReactNode;
  tagBg: string;
  tagText: string;
  tagBorder: string;
};

const TODO_PRIORITY_META: Record<DashboardTodoItem["priority"], PriorityVisual> = {
  urgent: {
    label: DASHBOARD_PAGE_COPY.labels.emergency,
    dotColor: "#ff4d4f",
    icon: <ExclamationCircleOutlined />,
    tagBg: "#fff1f0",
    tagText: "#a8071a",
    tagBorder: "#ffa39e",
  },
  important: {
    label: DASHBOARD_PAGE_COPY.labels.important,
    dotColor: "#fa8c16",
    icon: <WarningOutlined />,
    tagBg: "#fff7e6",
    tagText: "#ad4e00",
    tagBorder: "#ffd591",
  },
  normal: {
    label: DASHBOARD_PAGE_COPY.labels.normal,
    dotColor: "#1677ff",
    icon: <InfoCircleOutlined />,
    tagBg: "#e6f4ff",
    tagText: "#0958d9",
    tagBorder: "#91caff",
  },
};

export function Section02TodoSection({
  todoItems,
  loading = false,
  error = null,
  onRetry,
  onOpenTodo,
}: Section02TodoSectionProps) {
  const totalCount = todoItems.reduce((sum, item) => sum + item.count, 0);

  const handleCardKeyDown = (event: KeyboardEvent<HTMLDivElement>, href: DashboardRouteTarget) => {
    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }
    event.preventDefault();
    onOpenTodo(href);
  };

  return (
    <Card
      className={styles.sectionCard}
      size="small"
      title={
        <div className={styles.sectionHeaderRow}>
          <Space>
            <span className={styles.leftAccentIcon}>
              <AimOutlined />
            </span>
            <Typography.Text strong>{DASHBOARD_PAGE_COPY.sections.todo.cardTitle}</Typography.Text>
          </Space>
          <Typography.Text type="secondary">{totalCount > 0 ? `共 ${totalCount} 项` : "暂无待办"}</Typography.Text>
        </div>
      }
    >
      {loading ? <LoadingState compact message="加载待办事项" /> : null}
      {!loading && error ? <ErrorState compact message="待办事项加载失败" details={error} actionLabel="重试" onAction={onRetry} /> : null}
      {!loading && !error && todoItems.length === 0 ? <EmptyState compact description="暂无待办事项" /> : null}
      {!loading && !error && todoItems.length > 0 ? (
      <Row gutter={[12, 12]}>
        {todoItems.map((item) => (
          <Col key={item.key} xs={24} md={12}>
            <Card
              className={styles.todoCard}
              bordered={false}
              hoverable
              role="button"
              tabIndex={0}
              onClick={() => onOpenTodo(item.href)}
              onKeyDown={(event) => handleCardKeyDown(event, item.href)}
            >
              <Space direction="vertical" size={8} style={{ width: "100%" }}>
                <Space align="start" className={styles.todoTitleRow}>
                  <span
                    className={styles.dot}
                    style={{ background: TODO_PRIORITY_META[item.priority].dotColor }}
                    aria-hidden
                  />
                  <div style={{ flex: 1 }}>
                    <Space align="center" size={8}>
                      <Typography.Text strong>{item.title}</Typography.Text>
                      <Badge count={item.count} />
                    </Space>
                    <Tag
                      style={{
                        backgroundColor: TODO_PRIORITY_META[item.priority].tagBg,
                        color: TODO_PRIORITY_META[item.priority].tagText,
                        borderColor: TODO_PRIORITY_META[item.priority].tagBorder,
                      }}
                    >
                      <Space size={4} align="center">
                        {TODO_PRIORITY_META[item.priority].icon}
                        {TODO_PRIORITY_META[item.priority].label}
                      </Space>
                    </Tag>
                  </div>
                </Space>

                <Typography.Text type="secondary">{item.description}</Typography.Text>

                <Button
                  type="link"
                  icon={<ArrowRightOutlined />}
                  size="small"
                  style={{ width: "fit-content", padding: 0 }}
                  onClick={(event) => {
                    event.stopPropagation();
                    onOpenTodo(item.href);
                  }}
                >
                  {item.actionLabel}
                </Button>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>
      ) : null}
    </Card>
  );
}
