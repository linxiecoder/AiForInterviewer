import { Space, Tag, Typography } from "antd";

export type StatusType =
  | "ready"
  | "running"
  | "disabled"
  | "error"
  | "warning"
  | "loading"
  | "insufficient"
  | "success";

type StatusBadgeProps = {
  status: StatusType;
  label?: string;
  description?: string;
  compact?: boolean;
};

function colorFromStatus(status: StatusType): string {
  switch (status) {
    case "ready":
      return "green";
    case "running":
      return "blue";
    case "loading":
      return "processing";
    case "error":
      return "red";
    case "warning":
      return "orange";
    case "insufficient":
      return "gold";
    case "success":
      return "success";
    case "disabled":
    default:
      return "default";
  }
}

export function StatusBadge({ status, label, description, compact = false }: StatusBadgeProps) {
  const text = label ?? status;

  if (description === undefined) {
    return <Tag color={colorFromStatus(status)}>{text}</Tag>;
  }

  return (
    <Space direction={compact ? "horizontal" : "vertical"} size={4}>
      <Tag color={colorFromStatus(status)}>{text}</Tag>
      <Typography.Text type="secondary" style={{ fontSize: compact ? 12 : 13 }}>
        {description}
      </Typography.Text>
    </Space>
  );
}
