import { Button, Alert, Card, Typography } from "antd";
import { useMemo, type ReactNode } from "react";
import { ErrorState } from "../../../shared/ui/ErrorState";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { LoadingState } from "../../../shared/ui/LoadingState";
import { DASHBOARD_PAGE_COPY } from "../model/dashboardCopy";
import type {
  DashboardFrameMode,
  DashboardSectionState,
} from "../model/dashboardSections";

type DashboardFrameProps = {
  title: string;
  state: DashboardSectionState;
  children: ReactNode;
  disabledReason?: string;
  frameMode: DashboardFrameMode;
};

export function DashboardFrame({
  title,
  state,
  children,
  disabledReason,
  frameMode,
}: DashboardFrameProps) {
  const normalizedDisabledReason = useMemo(
    () => disabledReason ?? DASHBOARD_PAGE_COPY.states.disabledPrefix,
    [disabledReason],
  );

  if (state === "loading") {
    return (
      <LoadingState
        compact
        message={DASHBOARD_PAGE_COPY.states.loading}
        reason={DASHBOARD_PAGE_COPY.states.loadingReason}
        details={DASHBOARD_PAGE_COPY.states.loadingDetails}
      />
    );
  }

  if (state === "error") {
    return (
      <ErrorState
        compact
        message={`${title}加载失败`}
        reason={`${DASHBOARD_PAGE_COPY.states.errorRecoverHint}（frame=${frameMode}）。`}
        details={`${DASHBOARD_PAGE_COPY.states.errorRecoverHint} 可先关闭异常态返回默认。`}
        actionLabel="返回默认"
        onAction={() => {
          const params = new URLSearchParams(window.location.search);
          params.delete("frame");
          const nextSearch = params.toString();
          const nextUrl = `${window.location.pathname}${nextSearch ? `?${nextSearch}` : ""}${window.location.hash || ""}`;
          window.history.replaceState({}, "", nextUrl);
          window.dispatchEvent(new PopStateEvent("popstate"));
        }}
        description={<Typography.Text type="secondary">当前为占位态，仅表达状态语义，不影响真实数据。</Typography.Text>}
      />
    );
  }

  if (state === "empty") {
    return (
      <EmptyState
        compact
        title={`${title}：空态`}
        description={`当前无可展示记录。${DASHBOARD_PAGE_COPY.states.placeholderButton} 为占位态。`}
        reason={DASHBOARD_PAGE_COPY.states.emptyReason}
        action={
          <Button size="small" type="dashed" disabled>
            {DASHBOARD_PAGE_COPY.states.placeholderButton}
          </Button>
        }
      />
    );
  }

  if (state === "insufficient") {
    return (
      <Card size="small" bordered={false}>
        <Alert
          type="warning"
          showIcon
          message={DASHBOARD_PAGE_COPY.states.insufficientPrefix}
          description={`${title}：缺少前置资料，当前仅提供结构提示。${normalizedDisabledReason ? `（${normalizedDisabledReason}）` : ""}`}
        />
      </Card>
    );
  }

  if (state === "disabled") {
    return (
      <Card size="small" bordered={false}>
        <Alert
          type="info"
          showIcon
          message={DASHBOARD_PAGE_COPY.sections.empty.title}
          description={normalizedDisabledReason}
        />
      </Card>
    );
  }

  return <>{children}</>;
}
