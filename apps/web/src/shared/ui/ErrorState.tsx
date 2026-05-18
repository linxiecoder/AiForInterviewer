import { Alert, Button, Typography } from "antd";
import type { ReactNode } from "react";

type ErrorStateProps = {
  message: string;
  details?: string;
  reason?: string;
  actionLabel?: string;
  onAction?: () => void;
  compact?: boolean;
  description?: ReactNode;
  action?: ReactNode;
};

export function ErrorState({
  message,
  details,
  reason,
  actionLabel,
  onAction,
  compact = false,
  description,
  action,
}: ErrorStateProps) {
  const content = details ?? reason;

  return (
    <div
      style={
        compact
          ? { width: "100%", minHeight: 180, display: "grid", placeItems: "center", padding: 8 }
          : { minHeight: "100vh", display: "grid", placeItems: "center", padding: 24 }
      }
    >
      <div style={{ width: compact ? "100%" : "min(100%, 520px)" }}>
        <Alert
          type="error"
          showIcon
          message={message}
          description={
            <div>
              {description ?? (content ? <Typography.Paragraph>{content}</Typography.Paragraph> : null)}
              {!content && !description ? (
                <Typography.Paragraph type="secondary">
                  说明：当前为高保真 Shell 占位态，不依赖后端请求。
                </Typography.Paragraph>
              ) : null}
            </div>
          }
        />
        {onAction || action ? (
          <div style={{ marginTop: 16 }}>
            {action ?? (
              <Button type="primary" onClick={onAction}>
                {actionLabel ?? "返回"}
              </Button>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}
