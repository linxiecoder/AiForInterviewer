import { type Key, useEffect, useMemo, useState } from "react";
import { Button, Card, Descriptions, Drawer, Input, Modal, Select, Space, Table, Tag, Tooltip, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { EyeOutlined, PlayCircleOutlined, ReloadOutlined, SearchOutlined, UndoOutlined } from "@ant-design/icons";
import { AppShell } from "../../widgets/app-shell/AppShell";
import { useRouteController } from "../../app/routes/router";
import { fetchWeakness, fetchWeaknesses, updateWeaknessStatus } from "../../entities/weakness/api/weaknessApi";
import type { WeaknessDetail, WeaknessRef, WeaknessSummary } from "../../entities/weakness/model/types";
import { isApiHttpError } from "../../shared/api/errors";
import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorState } from "../../shared/ui/ErrorState";
import { LoadingState } from "../../shared/ui/LoadingState";

export const WEAKNESS_PAGE_TABLE_COLUMN_KEYS = ["selection", "title", "source", "severity", "status", "updated_at", "actions"] as const;
export const WEAKNESS_PAGE_VIEW_STATES = ["loading", "empty", "error", "loaded"] as const;
export const WEAKNESS_STATUS_ACTIONS = ["mark_low_priority", "mark_ignored", "mark_resolved", "reopen"] as const;
export const WEAKNESS_DETAIL_SECTIONS = ["evidence", "training_actions", "related_records", "status_history_hint"] as const;
export const WEAKNESS_SELECTED_ACTION_TARGET = "interview_entry_without_prefill" as const;
export const WEAKNESS_PAGE_TOOLBAR_CONTROL_ORDER = ["primary_action", "filters", "refresh", "search"] as const;
export const WEAKNESS_PAGE_SEARCH_PLACEHOLDER = "搜索薄弱项" as const;

const WEAKNESS_STATUS_OPTIONS = [
  { value: "weakness_confirmed", label: "已确认" },
  { value: "low_priority", label: "低优先级" },
  { value: "ignored", label: "已忽略" },
  { value: "resolved", label: "已解决" },
  { value: "reopened", label: "再次暴露" },
] as const;

const WEAKNESS_SEVERITY_OPTIONS = [
  { value: "low", label: "低" },
  { value: "medium", label: "中" },
  { value: "high", label: "高" },
  { value: "critical", label: "严重" },
] as const;

function toDisplayDate(raw: string): string {
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) {
    return raw || "-";
  }
  return date.toLocaleString();
}

function toErrorMessage(error: unknown, fallback: string): string {
  if (isApiHttpError(error)) {
    return error.safeMessage;
  }
  if (error instanceof Error) {
    return error.message || fallback;
  }
  return fallback;
}

function refLabel(ref: WeaknessRef): string {
  const type = typeof ref.resource_type === "string" ? ref.resource_type : "source";
  const id = typeof ref.resource_id === "string" ? ref.resource_id : "";
  const label = typeof ref.label === "string" ? ref.label : "";
  return label || [type, id].filter(Boolean).join(":") || "-";
}

function renderRefs(refs: readonly WeaknessRef[] | undefined) {
  if (!refs || refs.length === 0) {
    return <Typography.Text type="secondary">-</Typography.Text>;
  }
  return (
    <Space size={[4, 4]} wrap>
      {refs.slice(0, 3).map((ref, index) => (
        <Tag key={`${refLabel(ref)}-${index}`}>{refLabel(ref)}</Tag>
      ))}
      {refs.length > 3 ? <Tag>+{refs.length - 3}</Tag> : null}
    </Space>
  );
}

function renderSeverity(severity: string | null | undefined) {
  if (!severity) {
    return <Typography.Text type="secondary">-</Typography.Text>;
  }
  const color = severity === "critical" || severity === "high" ? "red" : severity === "medium" ? "orange" : "green";
  const label = WEAKNESS_SEVERITY_OPTIONS.find((item) => item.value === severity)?.label ?? severity;
  return <Tag color={color}>{label}</Tag>;
}

function renderStatus(status: string) {
  const color = status === "resolved" ? "green" : status === "ignored" ? "default" : status === "reopened" ? "red" : "blue";
  const label = WEAKNESS_STATUS_OPTIONS.find((item) => item.value === status)?.label ?? status;
  return <Tag color={color}>{label}</Tag>;
}

function statusFromAction(action: (typeof WEAKNESS_STATUS_ACTIONS)[number]): string {
  switch (action) {
    case "mark_low_priority":
      return "low_priority";
    case "mark_ignored":
      return "ignored";
    case "mark_resolved":
      return "resolved";
    case "reopen":
      return "reopened";
  }
}

function actionLabel(action: (typeof WEAKNESS_STATUS_ACTIONS)[number]): string {
  switch (action) {
    case "mark_low_priority":
      return "低优先级";
    case "mark_ignored":
      return "忽略";
    case "mark_resolved":
      return "解决";
    case "reopen":
      return "重开";
  }
}

export function WeaknessPage() {
  const { navigate } = useRouteController();
  const [weaknesses, setWeaknesses] = useState<WeaknessSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [keyword, setKeyword] = useState("");
  const [submittedKeyword, setSubmittedKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [severityFilter, setSeverityFilter] = useState<string | undefined>();
  const [selectedRowKeys, setSelectedRowKeys] = useState<Key[]>([]);
  const [polishModalOpen, setPolishModalOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [selectedWeakness, setSelectedWeakness] = useState<WeaknessDetail | null>(null);
  const [actionWeaknessId, setActionWeaknessId] = useState<string | null>(null);

  const selectedWeaknesses = useMemo(
    () => weaknesses.filter((weakness) => selectedRowKeys.includes(weakness.weakness_id)),
    [selectedRowKeys, weaknesses],
  );

  const loadWeaknesses = async () => {
    setLoading(true);
    setError(null);
    try {
      const nextWeaknesses = await fetchWeaknesses({
        status: statusFilter,
        severity: severityFilter,
        q: submittedKeyword,
      });
      setWeaknesses(nextWeaknesses);
      setSelectedRowKeys((current) =>
        current.filter((key) => nextWeaknesses.some((weakness) => weakness.weakness_id === key)),
      );
    } catch (loadError) {
      setError(toErrorMessage(loadError, "薄弱项列表加载失败"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadWeaknesses();
  }, [statusFilter, severityFilter, submittedKeyword]);

  const openDetail = async (weaknessId: string) => {
    setDetailOpen(true);
    setSelectedWeakness(null);
    setDetailLoading(true);
    setDetailError(null);
    try {
      setSelectedWeakness(await fetchWeakness(weaknessId));
    } catch (loadError) {
      setDetailError(toErrorMessage(loadError, "薄弱项详情加载失败"));
    } finally {
      setDetailLoading(false);
    }
  };

  const runStatusAction = async (
    weakness: WeaknessSummary | WeaknessDetail,
    action: (typeof WEAKNESS_STATUS_ACTIONS)[number],
  ) => {
    setActionWeaknessId(weakness.weakness_id);
    try {
      const updated = await updateWeaknessStatus(weakness.weakness_id, statusFromAction(action));
      message.success("状态已更新");
      setSelectedWeakness((current) => current?.weakness_id === updated.weakness_id ? updated : current);
      await loadWeaknesses();
    } catch (actionError) {
      message.error(toErrorMessage(actionError, "薄弱项状态更新失败"));
    } finally {
      setActionWeaknessId(null);
    }
  };

  const columns: ColumnsType<WeaknessSummary> = [
    {
      title: "薄弱项",
      dataIndex: "title",
      key: "title",
      width: 280,
      render: (_value, record) => (
        <Button type="link" onClick={() => openDetail(record.weakness_id)}>
          {record.title || record.weakness_id}
        </Button>
      ),
    },
    {
      title: "来源",
      dataIndex: "source_refs",
      key: "source",
      width: 220,
      render: (refs: WeaknessRef[]) => renderRefs(refs),
    },
    {
      title: "严重程度",
      dataIndex: "severity",
      key: "severity",
      width: 120,
      render: renderSeverity,
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 120,
      render: renderStatus,
    },
    {
      title: "更新时间",
      dataIndex: "updated_at",
      key: "updated_at",
      width: 180,
      render: toDisplayDate,
    },
    {
      title: "操作",
      key: "actions",
      fixed: "right",
      width: 156,
      render: (_value, record) => (
        <Space size={4}>
          <Tooltip title="查看">
            <Button shape="circle" icon={<EyeOutlined />} onClick={() => openDetail(record.weakness_id)} />
          </Tooltip>
          <Tooltip title="标记解决">
            <Button
              shape="circle"
              icon={<UndoOutlined />}
              loading={actionWeaknessId === record.weakness_id}
              onClick={() => runStatusAction(record, "mark_resolved")}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <AppShell>
      <Space direction="vertical" size={16} style={{ width: "100%" }}>
        <Card>
          <div
            style={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 12,
              flexWrap: "wrap",
            }}
          >
            <Space wrap>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                disabled={selectedRowKeys.length === 0}
                onClick={() => setPolishModalOpen(true)}
              >
                进入模拟面试
              </Button>
              <Select
                allowClear
                placeholder="状态"
                options={[...WEAKNESS_STATUS_OPTIONS]}
                value={statusFilter}
                onChange={setStatusFilter}
                style={{ width: 160 }}
              />
              <Select
                allowClear
                placeholder="严重程度"
                options={[...WEAKNESS_SEVERITY_OPTIONS]}
                value={severityFilter}
                onChange={setSeverityFilter}
                style={{ width: 160 }}
              />
              <Tooltip title="刷新">
                <Button icon={<ReloadOutlined />} onClick={loadWeaknesses}>
                  刷新
                </Button>
              </Tooltip>
            </Space>
            <Input.Search
              allowClear
              enterButton={<SearchOutlined aria-label="搜索" />}
              placeholder={WEAKNESS_PAGE_SEARCH_PLACEHOLDER}
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              onSearch={(value) => {
                const nextKeyword = value.trim();
                setKeyword(nextKeyword);
                setSubmittedKeyword(nextKeyword);
              }}
              style={{ width: 320, maxWidth: "100%", marginLeft: "auto" }}
            />
          </div>
        </Card>

        <Card>
          {loading ? <LoadingState compact message="加载薄弱项" /> : null}
          {!loading && error ? <ErrorState compact message="薄弱项列表加载失败" details={error} actionLabel="重试" onAction={loadWeaknesses} /> : null}
          {!loading && !error && weaknesses.length === 0 ? (
            <EmptyState compact description={submittedKeyword || statusFilter || severityFilter ? "无匹配薄弱项" : "暂无薄弱项"} />
          ) : null}
          {!loading && !error && weaknesses.length > 0 ? (
            <Table
              rowKey="weakness_id"
              rowSelection={{ selectedRowKeys, onChange: setSelectedRowKeys }}
              columns={columns}
              dataSource={weaknesses}
              pagination={{ pageSize: 10, showSizeChanger: true }}
              scroll={{ x: 1088 }}
            />
          ) : null}
        </Card>
      </Space>

      <Drawer
        width={580}
        title={selectedWeakness?.title || "薄弱项详情"}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
      >
        {detailLoading ? <LoadingState compact message="加载薄弱项详情" /> : null}
        {!detailLoading && detailError ? <ErrorState compact message="薄弱项详情加载失败" details={detailError} /> : null}
        {!detailLoading && !detailError && selectedWeakness ? (
          <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="状态">{renderStatus(selectedWeakness.status)}</Descriptions.Item>
              <Descriptions.Item label="严重程度">{renderSeverity(selectedWeakness.severity)}</Descriptions.Item>
              <Descriptions.Item label="维度">{selectedWeakness.dimension || "-"}</Descriptions.Item>
              <Descriptions.Item label="来源">{renderRefs(selectedWeakness.source_refs)}</Descriptions.Item>
              <Descriptions.Item label="证据">{renderRefs(selectedWeakness.evidence_refs)}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{toDisplayDate(selectedWeakness.updated_at)}</Descriptions.Item>
            </Descriptions>
            <Typography.Paragraph>{selectedWeakness.summary || "-"}</Typography.Paragraph>
            <Card size="small" title="建议动作">
              {selectedWeakness.suggested_training_actions.length === 0 ? (
                <Typography.Text type="secondary">-</Typography.Text>
              ) : (
                <Space wrap>
                  {selectedWeakness.suggested_training_actions.map((action) => <Tag key={action}>{action}</Tag>)}
                </Space>
              )}
            </Card>
            <Card size="small" title="关联记录">
              <Space direction="vertical" style={{ width: "100%" }}>
                <div>{renderRefs(selectedWeakness.related_refs.sessions)}</div>
                <div>{renderRefs(selectedWeakness.related_refs.feedback)}</div>
                <div>{renderRefs(selectedWeakness.related_refs.questions)}</div>
                <div>{renderRefs(selectedWeakness.related_refs.answers)}</div>
              </Space>
            </Card>
            <Space wrap>
              {WEAKNESS_STATUS_ACTIONS.map((action) => (
                <Button
                  key={action}
                  loading={actionWeaknessId === selectedWeakness.weakness_id}
                  onClick={() => runStatusAction(selectedWeakness, action)}
                >
                  {actionLabel(action)}
                </Button>
              ))}
            </Space>
          </Space>
        ) : null}
      </Drawer>

      <Modal
        title="进入模拟面试"
        open={polishModalOpen}
        onCancel={() => setPolishModalOpen(false)}
        okText="进入模拟面试"
        cancelText="取消"
        onOk={() => {
          setPolishModalOpen(false);
          navigate("/interview");
        }}
      >
        <Typography.Paragraph type="secondary">
          当前仅打开模拟面试入口，不自动携带已选薄弱项。
        </Typography.Paragraph>
        <Space size={[4, 4]} wrap>
          {selectedWeaknesses.map((weakness) => (
            <Tag key={weakness.weakness_id}>{weakness.title || weakness.weakness_id}</Tag>
          ))}
        </Space>
      </Modal>
    </AppShell>
  );
}
