import { Spin, Typography } from "antd";
import type { ReactNode } from "react";

type LoadingStateProps = {
  message?: string;
  details?: string;
  compact?: boolean;
  description?: ReactNode;
  reason?: string;
  action?: ReactNode;
};

export function LoadingState({
  message = "加载中",
  details,
  compact = false,
  description,
  action,
  reason,
}: LoadingStateProps) {
  const helperText = description ?? details;

  const containerStyle: React.CSSProperties = compact
    ? {
        minHeight: 180,
        display: "grid",
        placeItems: "center",
        padding: 24,
      }
    : {
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        color: "#1f2937",
        padding: 24,
      };

  return (
    <div style={containerStyle}>
      <div style={{ textAlign: "center" }}>
        <Spin size="large" />
        <div style={{ marginTop: 12 }}>
          <Typography.Text strong>{message}</Typography.Text>
        </div>
        {reason ? (
          <Typography.Text type="secondary" style={{ marginTop: 8, fontSize: 12 }}>
            {reason}
          </Typography.Text>
        ) : null}
        {helperText ? (
          <div style={{ marginTop: 8 }}>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              {helperText}
            </Typography.Text>
          </div>
        ) : null}
        {action ? (
          <div style={{ marginTop: 16 }}>
            {action}
          </div>
        ) : null}
      </div>
    </div>
  );
}
