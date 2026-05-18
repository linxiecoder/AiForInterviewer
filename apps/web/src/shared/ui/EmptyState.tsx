import { Button, Empty, type EmptyProps } from "antd";
import type { ReactNode } from "react";

type EmptyStateProps = {
  title?: string;
  description?: string;
  action?: ReactNode;
  compact?: boolean;
  icon?: EmptyProps["image"];
  reason?: string;
  actionLabel?: string;
  onAction?: () => void;
};

export function EmptyState({
  title,
  description = "当前暂无内容。",
  action,
  compact = false,
  icon,
  reason,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  const resolvedAction = action ??
    (onAction && actionLabel ? (
      <Button size="small" disabled>
        {actionLabel}
      </Button>
    ) : null);

  return (
    <div style={compact ? { padding: 16 } : { padding: 32 }}>
      <Empty image={icon} description={description} />
      {title ? <div style={{ marginTop: 4, textAlign: "center", color: "#4b5563" }}>{title}</div> : null}
      {reason ? <div style={{ marginTop: 8, textAlign: "center", color: "rgba(0, 0, 0, 0.45)" }}>{reason}</div> : null}
      {resolvedAction || action ? <div style={{ marginTop: 12, textAlign: "center" }}>{resolvedAction || action}</div> : null}
    </div>
  );
}
