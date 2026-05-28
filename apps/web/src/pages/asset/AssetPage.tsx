import { useEffect, useState } from "react";
import { Button, Card, Descriptions, Drawer, Form, Input, Select, Space, Table, Tag, Tooltip, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { EyeOutlined, PlusOutlined, ReloadOutlined, SearchOutlined, StopOutlined, UndoOutlined } from "@ant-design/icons";
import { AppShell } from "../../widgets/app-shell/AppShell";
import { archiveAsset, createAsset, fetchAsset, fetchAssets, unarchiveAsset } from "../../entities/asset/api/assetApi";
import type { AssetDetail, AssetRef, AssetSummary } from "../../entities/asset/model/types";
import { isApiHttpError } from "../../shared/api/errors";
import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorState } from "../../shared/ui/ErrorState";
import { LoadingState } from "../../shared/ui/LoadingState";

export const ASSET_PAGE_TABLE_COLUMN_KEYS = ["title", "asset_type", "source", "status", "updated_at", "actions"] as const;
export const ASSET_PAGE_VIEW_STATES = ["loading", "empty", "error", "loaded"] as const;
export const ASSET_STATUS_ACTIONS = ["archive", "unarchive"] as const;
export const ASSET_DETAIL_ACTIONS = ["view_source", "archive", "unarchive"] as const;
export const ASSET_TYPE_FILTER_KIND = "asset_type_and_source" as const;
export const ASSET_PAGE_TOOLBAR_CONTROL_ORDER = ["primary_action", "filters", "refresh", "search"] as const;
export const ASSET_PAGE_SEARCH_PLACEHOLDER = "搜索资产" as const;

const ASSET_STATUS_OPTIONS = [
  { value: "asset_confirmed", label: "已确认" },
  { value: "asset_archived", label: "已归档" },
  { value: "disabled", label: "不可用" },
] as const;

const ASSET_TYPE_OPTIONS = [
  { value: "project_story", label: "项目表达" },
  { value: "self_intro", label: "自我介绍" },
  { value: "technical_note", label: "技术要点" },
  { value: "behavior_story", label: "行为面素材" },
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

function refLabel(ref: AssetRef): string {
  const type = typeof ref.resource_type === "string" ? ref.resource_type : "source";
  const id = typeof ref.resource_id === "string" ? ref.resource_id : "";
  const label = typeof ref.label === "string" ? ref.label : "";
  return label || [type, id].filter(Boolean).join(":") || "-";
}

function renderRefs(refs: readonly AssetRef[] | undefined) {
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

function renderStatus(status: string) {
  const color = status === "asset_confirmed" ? "green" : status === "asset_archived" ? "default" : "orange";
  const label = ASSET_STATUS_OPTIONS.find((item) => item.value === status)?.label ?? status;
  return <Tag color={color}>{label}</Tag>;
}

export function AssetPage() {
  const [createForm] = Form.useForm();
  const [assets, setAssets] = useState<AssetSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [keyword, setKeyword] = useState("");
  const [submittedKeyword, setSubmittedKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [assetTypeFilter, setAssetTypeFilter] = useState<string | undefined>();
  const [createOpen, setCreateOpen] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<AssetDetail | null>(null);
  const [actionAssetId, setActionAssetId] = useState<string | null>(null);

  const loadAssets = async () => {
    setLoading(true);
    setError(null);
    try {
      const nextAssets = await fetchAssets({
        status: statusFilter,
        asset_type: assetTypeFilter,
        q: submittedKeyword,
      });
      setAssets(nextAssets);
    } catch (loadError) {
      setError(toErrorMessage(loadError, "资产列表加载失败"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadAssets();
  }, [statusFilter, assetTypeFilter, submittedKeyword]);

  const openCreate = () => {
    createForm.resetFields();
    setCreateError(null);
    setCreateOpen(true);
  };

  const submitCreate = async () => {
    setCreateLoading(true);
    setCreateError(null);
    try {
      const values = await createForm.validateFields();
      await createAsset({
        title: String(values.title ?? "").trim(),
        asset_type: String(values.asset_type ?? "").trim(),
        content: String(values.content ?? "").trim(),
        summary: values.summary ? String(values.summary).trim() : undefined,
      });
      message.success("资产已新增");
      setCreateOpen(false);
      createForm.resetFields();
      await loadAssets();
    } catch (createAssetError) {
      if (typeof createAssetError === "object" && createAssetError !== null && "errorFields" in createAssetError) {
        return;
      }
      const messageText = toErrorMessage(createAssetError, "资产新增失败");
      setCreateError(messageText);
      message.error(messageText);
    } finally {
      setCreateLoading(false);
    }
  };

  const openDetail = async (assetId: string) => {
    setDetailOpen(true);
    setSelectedAsset(null);
    setDetailLoading(true);
    setDetailError(null);
    try {
      setSelectedAsset(await fetchAsset(assetId));
    } catch (loadError) {
      setDetailError(toErrorMessage(loadError, "资产详情加载失败"));
    } finally {
      setDetailLoading(false);
    }
  };

  const runStatusAction = async (asset: AssetSummary | AssetDetail) => {
    setActionAssetId(asset.asset_id);
    try {
      const updated = asset.status === "asset_archived"
        ? await unarchiveAsset(asset.asset_id)
        : await archiveAsset(asset.asset_id);
      message.success(updated.status === "asset_archived" ? "已归档" : "已取消归档");
      setSelectedAsset((current) => current?.asset_id === updated.asset_id ? updated : current);
      await loadAssets();
    } catch (actionError) {
      message.error(toErrorMessage(actionError, "资产状态更新失败"));
    } finally {
      setActionAssetId(null);
    }
  };

  const columns: ColumnsType<AssetSummary> = [
    {
      title: "资产",
      dataIndex: "title",
      key: "title",
      width: 260,
      render: (_value, record) => (
        <Button type="link" onClick={() => openDetail(record.asset_id)}>
          {record.title || record.asset_id}
        </Button>
      ),
    },
    {
      title: "类型",
      dataIndex: "asset_type",
      key: "asset_type",
      width: 140,
      render: (value: string | null) => value ? <Tag>{value}</Tag> : <Typography.Text type="secondary">-</Typography.Text>,
    },
    {
      title: "来源",
      dataIndex: "source_refs",
      key: "source",
      width: 220,
      render: (refs: AssetRef[]) => renderRefs(refs),
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
      width: 112,
      render: (_value, record) => (
        <Space size={4}>
          <Tooltip title="查看">
            <Button shape="circle" icon={<EyeOutlined />} onClick={() => openDetail(record.asset_id)} />
          </Tooltip>
          <Tooltip title={record.status === "asset_archived" ? "取消归档" : "归档"}>
            <Button
              shape="circle"
              icon={record.status === "asset_archived" ? <UndoOutlined /> : <StopOutlined />}
              loading={actionAssetId === record.asset_id}
              onClick={() => runStatusAction(record)}
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
              <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
                新增资产
              </Button>
              <Select
                allowClear
                placeholder="资产类型"
                options={[...ASSET_TYPE_OPTIONS]}
                value={assetTypeFilter}
                onChange={setAssetTypeFilter}
                style={{ width: 180 }}
              />
              <Select
                allowClear
                placeholder="状态"
                options={[...ASSET_STATUS_OPTIONS]}
                value={statusFilter}
                onChange={setStatusFilter}
                style={{ width: 160 }}
              />
              <Tooltip title="刷新">
                <Button icon={<ReloadOutlined />} onClick={loadAssets}>
                  刷新
                </Button>
              </Tooltip>
            </Space>
            <Input.Search
              allowClear
              enterButton={<SearchOutlined aria-label="搜索" />}
              placeholder={ASSET_PAGE_SEARCH_PLACEHOLDER}
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
          {loading ? <LoadingState compact message="加载资产" /> : null}
          {!loading && error ? <ErrorState compact message="资产列表加载失败" details={error} actionLabel="重试" onAction={loadAssets} /> : null}
          {!loading && !error && assets.length === 0 ? (
            <EmptyState compact description={submittedKeyword || statusFilter || assetTypeFilter ? "无匹配资产" : "暂无资产"} />
          ) : null}
          {!loading && !error && assets.length > 0 ? (
            <Table
              rowKey="asset_id"
              columns={columns}
              dataSource={assets}
              pagination={{ pageSize: 10, showSizeChanger: true }}
              scroll={{ x: 1032 }}
            />
          ) : null}
        </Card>
      </Space>

      <Drawer
        width={560}
        title="新增资产"
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        extra={(
          <Space>
            <Button onClick={() => setCreateOpen(false)}>取消</Button>
            <Button type="primary" loading={createLoading} onClick={submitCreate}>
              提交
            </Button>
          </Space>
        )}
      >
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <Typography.Paragraph type="secondary">
            提交后会写入资产库，并进入知识库索引。
          </Typography.Paragraph>
          {createError ? <ErrorState compact message="资产新增失败" details={createError} /> : null}
          <Form form={createForm} layout="vertical" disabled={createLoading}>
            <Form.Item name="title" label="资产标题" rules={[{ required: true, whitespace: true, message: "请输入资产标题" }]}>
              <Input maxLength={160} />
            </Form.Item>
            <Form.Item name="asset_type" label="资产类型" rules={[{ required: true, message: "请选择资产类型" }]}>
              <Select options={[...ASSET_TYPE_OPTIONS]} />
            </Form.Item>
            <Form.Item name="content" label="资产文本内容" rules={[{ required: true, whitespace: true, message: "请输入资产文本内容" }]}>
              <Input.TextArea rows={10} maxLength={20000} showCount />
            </Form.Item>
            <Form.Item name="summary" label="摘要">
              <Input.TextArea rows={3} maxLength={2000} showCount />
            </Form.Item>
          </Form>
        </Space>
      </Drawer>

      <Drawer
        width={560}
        title={selectedAsset?.title || "资产详情"}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        extra={selectedAsset ? (
          <Button
            icon={selectedAsset.status === "asset_archived" ? <UndoOutlined /> : <StopOutlined />}
            loading={actionAssetId === selectedAsset.asset_id}
            onClick={() => runStatusAction(selectedAsset)}
          >
            {selectedAsset.status === "asset_archived" ? "取消归档" : "归档"}
          </Button>
        ) : null}
      >
        {detailLoading ? <LoadingState compact message="加载资产详情" /> : null}
        {!detailLoading && detailError ? <ErrorState compact message="资产详情加载失败" details={detailError} /> : null}
        {!detailLoading && !detailError && selectedAsset ? (
          <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="状态">{renderStatus(selectedAsset.status)}</Descriptions.Item>
              <Descriptions.Item label="类型">{selectedAsset.asset_type || "-"}</Descriptions.Item>
              <Descriptions.Item label="来源">{renderRefs(selectedAsset.source_refs)}</Descriptions.Item>
              <Descriptions.Item label="证据">{renderRefs(selectedAsset.evidence_refs)}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{toDisplayDate(selectedAsset.updated_at)}</Descriptions.Item>
            </Descriptions>
            <Typography.Paragraph>{selectedAsset.summary || "-"}</Typography.Paragraph>
            <Typography.Paragraph style={{ whiteSpace: "pre-wrap" }}>
              {selectedAsset.content || "-"}
            </Typography.Paragraph>
            <Card size="small" title="版本">
              <Space direction="vertical" style={{ width: "100%" }}>
                {selectedAsset.versions.length === 0 ? <Typography.Text type="secondary">-</Typography.Text> : null}
                {selectedAsset.versions.map((version) => (
                  <div key={version.asset_version_id}>
                    <Typography.Text strong>v{version.version_number}</Typography.Text>
                    <Typography.Text type="secondary"> {toDisplayDate(version.updated_at)}</Typography.Text>
                    {version.edit_summary ? <Typography.Paragraph>{version.edit_summary}</Typography.Paragraph> : null}
                  </div>
                ))}
              </Space>
            </Card>
          </Space>
        ) : null}
      </Drawer>
    </AppShell>
  );
}
