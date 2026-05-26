import { AimOutlined, ArrowRightOutlined, ExclamationCircleOutlined, InfoCircleOutlined, WarningOutlined } from "@ant-design/icons";
import { Badge, Button, Card, Col, Row, Space, Tag, Typography } from "antd";
import type { ReactNode } from "react";
import { DASHBOARD_PAGE_COPY } from "../model/dashboardCopy";
import { TODO_ITEMS, type TodoItem } from "../model/dashboardPlaceholderData";

import styles from "./sectionStyles.module.css";

type Section02TodoSectionProps = {
  todoItems?: TodoItem[];
};

type PriorityVisual = {
  label: string;
  dotColor: string;
  icon: ReactNode;
  tagBg: string;
  tagText: string;
  tagBorder: string;
};

const TODO_PRIORITY_META: Record<TodoItem["priority"], PriorityVisual> = {
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

export function Section02TodoSection({ todoItems = TODO_ITEMS }: Section02TodoSectionProps) {
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
          <Typography.Text type="secondary">{DASHBOARD_PAGE_COPY.sections.todo.totalHint}</Typography.Text>
        </div>
      }
    >
      <Row gutter={[12, 12]}>
        {todoItems.map((item) => (
          <Col key={item.key} xs={24} md={12}>
            <Card className={styles.todoCard} bordered={false}>
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
                  disabled
                  style={{ width: "fit-content", padding: 0 }}
                >
                  {item.actionLabel}
                </Button>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>
    </Card>
  );
}
