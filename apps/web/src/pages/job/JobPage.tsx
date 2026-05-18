import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Col,
  Drawer,
  Empty,
  Form,
  Input,
  List,
  Modal,
  Row,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  Tooltip,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { CheckCircleOutlined, EditOutlined, EyeOutlined, InboxOutlined, PlusOutlined, ReloadOutlined } from "@ant-design/icons";
import { AppShell } from "../../widgets/app-shell/AppShell";
import type { ResumeApiState } from "../../entities/resume/api/resumeApi";
import { fetchResumeSummaries } from "../../entities/resume/api/resumeApi";
import { fetchJob, fetchJobs, createJob, updateJob, createBinding, removeBinding } from "../../entities/job/api/jobApi";
import type {
  JobBindingSummary,
  JobCreateRequest,
  JobDetail,
  JobResumeBinding,
  JobSummary,
  JobUpdateRequest,
  VersionRef,
} from "../../entities/job/model/types";
import { isApiHttpError, type ApiHttpError } from "../../shared/api/errors";
import { LoadingState } from "../../shared/ui/LoadingState";
import { ErrorState } from "../../shared/ui/ErrorState";
import { EmptyState } from "../../shared/ui/EmptyState";
import { useRouteController } from "../../app/routes/router";

type JobFormMode = "create" | "edit";

type JobFormValues = {
  title: string;
  company: string;
  department: string;
  application_status: string;
  responsibilitiesText: string;
  requirementsText: string;
  other_notes: string;
};

type UiErrorKind =
  | "unauthorized"
  | "permission_denied"
  | "not_found"
  | "conflict"
  | "validation"
  | "server"
  | "network"
  | "unexpected";

type UiError = {
  kind: UiErrorKind;
  message: string;
  actionLabel?: string;
};

type BindingMode = "idle" | "binding" | "unbinding";

const DEFAULT_APPLICATION_STATUS = "draft";
const TEXTAREA_ROWS = 4;

function toDisplayDate(raw: string): string {
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) {
    return raw;
  }
  return date.toLocaleString();
}

function splitList(raw: string | undefined): string[] {
  return (raw ?? "")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

function joinList(items: string[]): string {
  return items.join("\n");
}

function toFormValues(detail: JobDetail): JobFormValues {
  return {
    title: detail.title ?? "",
    company: detail.company ?? "",
    department: detail.department ?? "",
    application_status: detail.application_status,
    responsibilitiesText: joinList(detail.responsibilities),
    requirementsText: joinList(detail.requirements),
    other_notes: detail.other_notes ?? "",
  };
}

function toCreatePayload(values: JobFormValues): JobCreateRequest {
  return {
    title: values.title.trim(),
    company: values.company.trim() || undefined,
    department: values.department.trim() || undefined,
    responsibilities: splitList(values.responsibilitiesText),
    requirements: splitList(values.requirementsText),
    other_notes: values.other_notes.trim() || null,
    application_status: values.application_status || DEFAULT_APPLICATION_STATUS,
  };
}

function toUpdatePayload(
  values: JobFormValues,
  currentVersionRef: VersionRef,
): JobUpdateRequest {
  return {
    title: values.title.trim(),
    company: values.company.trim() || null,
    department: values.department.trim() || null,
    responsibilities: splitList(values.responsibilitiesText),
    requirements: splitList(values.requirementsText),
    other_notes: values.other_notes.trim() || null,
    application_status: values.application_status || DEFAULT_APPLICATION_STATUS,
    base_version_ref: currentVersionRef,
  };
}

function buildBindingLabel(binding: JobBindingSummary): string {
  if (binding.status !== "bound") {
    return "未绑定";
  }
  if (binding.resume_title) {
    return `已绑定 ${binding.resume_title}`;
  }
  if (binding.resume_id) {
    return `已绑定 ${binding.resume_id}`;
  }
  return "已绑定";
}

function parseApiError(error: unknown): UiError {
  if (isApiHttpError(error)) {
    const apiError = error as ApiHttpError;
    const code = apiError.code || "";
    if (apiError.status === 401) {
      return {
        kind: "unauthorized",
        message: "未登录或会话过期，请先登录。",
        actionLabel: "前往登录",
      };
    }
    if (apiError.status === 403 || apiError.status === 404 || code === "permission_denied") {
      return {
        kind: "permission_denied",
        message: "当前账号无权限访问该资源。",
      };
    }
    if (apiError.status === 409 || code === "stale_version_conflict" || code === "idempotency_conflict") {
      return {
        kind: "conflict",
        message: "发生版本冲突，请刷新后重试。",
      };
    }
    if (apiError.status === 422 || code === "validation_failed") {
      return {
        kind: "validation",
        message: apiError.safeMessage || "校验失败，请检查输入。",
      };
    }
    return {
      kind: apiError.status >= 500 ? "server" : "unexpected",
      message: apiError.safeMessage || "请求失败，请稍后重试。",
    };
  }
  if (error instanceof Error) {
    return { kind: "network", message: error.message || "请求失败，请稍后重试。" };
  }
  return { kind: "unexpected", message: "请求失败，请稍后重试。" };
}

function toErrorHint(error: UiError | null): string {
  if (error === null) {
    return "";
  }
  switch (error.kind) {
    case "unauthorized":
      return "请先重新登录后重试。";
    case "permission_denied":
      return "请确认账号权限、岗位归属范围与登录状态。";
    case "not_found":
      return "目标岗位可能已被删除或不在你的可见范围。";
    case "conflict":
      return "数据已被其他操作修改，建议重新加载后重试。";
    case "validation":
      return "请根据提示修正表单输入。";
    case "server":
      return "服务端返回异常，请稍后再试。";
    case "network":
      return "网络请求异常，请检查网络。";
    default:
      return "如持续失败，请记录页面状态并联系支持。";
  }
}

export function JobPage() {
  const { navigate } = useRouteController();

  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [isJobsLoading, setIsJobsLoading] = useState<boolean>(false);
  const [jobsError, setJobsError] = useState<UiError | null>(null);

  const [detailOpen, setDetailOpen] = useState<boolean>(false);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [detailError, setDetailError] = useState<UiError | null>(null);
  const [selectedJob, setSelectedJob] = useState<JobDetail | null>(null);

  const [formOpen, setFormOpen] = useState<boolean>(false);
  const [formMode, setFormMode] = useState<JobFormMode>("create");
  const [formLoading, setFormLoading] = useState<boolean>(false);
  const [formSubmitLoading, setFormSubmitLoading] = useState<boolean>(false);
  const [formError, setFormError] = useState<UiError | null>(null);
  const [editingTargetVersion, setEditingTargetVersion] = useState<VersionRef | null>(null);
  const [editingJobId, setEditingJobId] = useState<string | null>(null);
  const [isFormDirty, setIsFormDirty] = useState<boolean>(false);
  const [formInitialSignature, setFormInitialSignature] = useState<string>("");
  const [form] = Form.useForm<JobFormValues>();

  const [resumeState, setResumeState] = useState<ResumeApiState>({ kind: "ready", resumes: [] });
  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null);
  const [bindingMode, setBindingMode] = useState<BindingMode>("idle");
  const [bindingError, setBindingError] = useState<UiError | null>(null);
  const [bindingResult, setBindingResult] = useState<JobResumeBinding | null>(null);

  const [archivingJobId, setArchivingJobId] = useState<string | null>(null);

  const openCreateForm = () => {
    setFormMode("create");
    setEditingJobId(null);
    setEditingTargetVersion(null);
    setFormError(null);
    setSelectedResumeId(null);
    setBindingResult(null);
    setBindingError(null);
    const defaults = {
      title: "",
      company: "",
      department: "",
      application_status: DEFAULT_APPLICATION_STATUS,
      responsibilitiesText: "",
      requirementsText: "",
      other_notes: "",
    };
    setFormInitialSignature(JSON.stringify(defaults));
    setIsFormDirty(false);
    setFormLoading(false);
    form.setFieldsValue(defaults);
    setFormOpen(true);
  };

  const closeForm = () => {
    setFormOpen(false);
    setFormError(null);
    setIsFormDirty(false);
    form.resetFields();
  };

  const requestCloseForm = () => {
    if (formSubmitLoading || !isFormDirty) {
      closeForm();
      return;
    }

    Modal.confirm({
      title: "表单有未保存修改，确认关闭？",
      content: "未保存内容将丢失。",
      okText: "放弃",
      cancelText: "继续编辑",
      onOk: closeForm,
    });
  };

  const loadJobs = async () => {
    setIsJobsLoading(true);
    setJobsError(null);
    try {
      const list = await fetchJobs();
      setJobs(list);
    } catch (error) {
      setJobsError(parseApiError(error));
    } finally {
      setIsJobsLoading(false);
    }
  };

  const loadResumeState = async () => {
    const state = await fetchResumeSummaries();
    setResumeState(state);
    if (state.kind === "ready" && state.resumes.length > 0) {
      setSelectedResumeId((prev) => prev && state.resumes.some((item) => item.resume_id === prev) ? prev : state.resumes[0].resume_id);
    } else {
      setSelectedResumeId(null);
    }
  };

  const refreshEverything = async () => {
    await loadJobs();
    if (selectedJob !== null) {
      try {
        const jobDetail = await fetchJob(selectedJob.job_id);
        setSelectedJob(jobDetail);
      } catch {
        setSelectedJob(null);
      }
    }
  };

  const openJobDetail = async (jobId: string) => {
    setDetailOpen(true);
    setDetailLoading(true);
    setDetailError(null);
    setBindingError(null);
    setBindingResult(null);
    setBindingMode("idle");
    setFormError(null);
    try {
      const detail = await fetchJob(jobId);
      setSelectedJob(detail);
    } catch (error) {
      setDetailError(parseApiError(error));
      setSelectedJob(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const openJobEdit = async (jobId: string) => {
    setFormMode("edit");
    setFormLoading(true);
    setFormError(null);
    setEditingJobId(jobId);
    setBindingError(null);
    setBindingResult(null);
    setSelectedResumeId(null);
    try {
      const detail = await fetchJob(jobId);
      const values = toFormValues(detail);
      const signature = JSON.stringify(values);
      setEditingTargetVersion(detail.current_version_ref);
      setFormInitialSignature(signature);
      setIsFormDirty(false);
      form.setFieldsValue(values);
      setFormOpen(true);
    } catch (error) {
      const parsed = parseApiError(error);
      message.error(parsed.message);
    } finally {
      setFormLoading(false);
    }
  };

  const closeDetail = () => {
    setDetailOpen(false);
    setSelectedJob(null);
    setDetailError(null);
    setBindingError(null);
    setBindingMode("idle");
    setBindingResult(null);
    setSelectedResumeId(null);
  };

  const createNewJob = async (values: JobFormValues) => {
    const payload = toCreatePayload(values);
    const response = await createJob(payload);
    message.success(`岗位「${response.title}」创建成功。`);
    return response;
  };

  const saveJob = async () => {
    let values: JobFormValues;
    try {
      values = await form.validateFields();
    } catch {
      return;
    }

    if (formMode === "create") {
      setFormSubmitLoading(true);
      setFormError(null);
      try {
        await createNewJob(values);
        await loadJobs();
        setFormOpen(false);
        setFormError(null);
      } catch (error) {
        const parsed = parseApiError(error);
        setFormError(parsed);
      } finally {
        setFormSubmitLoading(false);
      }
      return;
    }

    if (editingJobId === null || editingTargetVersion === null) {
      setFormError({ kind: "unexpected", message: "缺少编辑版本基准，请重新打开编辑面板。" });
      return;
    }

    setFormSubmitLoading(true);
    setFormError(null);
    try {
      const payload = toUpdatePayload(values, editingTargetVersion);
      const response = await updateJob(editingJobId, payload);
      message.success(`岗位「${response.title}」更新成功。`);
      await refreshEverything();
      setFormOpen(false);
    } catch (error) {
      const parsed = parseApiError(error);
      setFormError(parsed);
      if (parsed.kind === "conflict") {
        message.warning("更新出现版本冲突，请刷新后重试。");
      }
    } finally {
      setFormSubmitLoading(false);
    }
  };

  const archiveJob = async (job: JobSummary) => {
    Modal.confirm({
      title: `确认归档岗位「${job.title}」？`,
      content: "归档后岗位状态将变为 archived，可在列表中保留历史记录。",
      okText: "确认归档",
      cancelText: "取消",
      onOk: async () => {
        setArchivingJobId(job.job_id);
        try {
          await updateJob(job.job_id, {
            status: "archived",
            base_version_ref: job.current_version_ref,
          });
          message.success(`岗位「${job.title}」已归档。`);
          await loadJobs();
          if (detailOpen && selectedJob?.job_id === job.job_id) {
            await openJobDetail(job.job_id);
          }
        } catch (error) {
          const parsed = parseApiError(error);
          message.error(parsed.message);
        } finally {
          setArchivingJobId(null);
        }
      },
    });
  };

  const getResumeSelectItems = () =>
    resumeState.kind === "ready"
      ? resumeState.resumes.map((item) => ({
          value: item.resume_id,
          label: item.title || item.resume_id,
        }))
      : [];

  const bindResumeToJob = async () => {
    if (selectedJob === null || selectedResumeId === null) {
      return;
    }
    setBindingMode("binding");
    setBindingError(null);
    try {
      const response = await createBinding({
        resume_id: selectedResumeId,
        job_id: selectedJob.job_id,
      });
      setBindingResult(response);
      message.success(`岗位绑定成功（${response.binding_id}）。`);
      const refreshed = await fetchJob(selectedJob.job_id);
      setSelectedJob(refreshed);
      setJobs((prev) =>
        prev.map((item) =>
          item.job_id === refreshed.job_id
            ? {
                ...item,
                binding_summary: refreshed.binding_summary,
                updated_at: refreshed.updated_at,
              }
            : item,
        ),
      );
    } catch (error) {
      const parsed = parseApiError(error);
      setBindingError(parsed);
    } finally {
      setBindingMode("idle");
    }
  };

  const unbindResumeFromJob = async () => {
    if (
      selectedJob === null
      || selectedJob.binding_summary.status !== "bound"
      || selectedJob.binding_summary.resume_job_binding_id == null
    ) {
      return;
    }
    const bindingId = selectedJob.binding_summary.resume_job_binding_id;
    setBindingMode("unbinding");
    setBindingError(null);
    try {
      const response = await removeBinding(bindingId);
      setBindingResult(response);
      message.success("绑定已解除。");
      const refreshed = await fetchJob(selectedJob.job_id);
      setSelectedJob(refreshed);
      setJobs((prev) =>
        prev.map((item) =>
          item.job_id === refreshed.job_id
            ? {
                ...item,
                binding_summary: refreshed.binding_summary,
                updated_at: refreshed.updated_at,
              }
            : item,
        ),
      );
    } catch (error) {
      const parsed = parseApiError(error);
      setBindingError(parsed);
    } finally {
      setBindingMode("idle");
    }
  };

  const onFormValuesChange = (_: unknown, allValues: JobFormValues) => {
    const signature = JSON.stringify({
      title: allValues.title?.trim() ?? "",
      company: allValues.company?.trim() ?? "",
      department: allValues.department?.trim() ?? "",
      application_status: allValues.application_status ?? DEFAULT_APPLICATION_STATUS,
      responsibilitiesText: (allValues.responsibilitiesText ?? "").trim(),
      requirementsText: (allValues.requirementsText ?? "").trim(),
      other_notes: (allValues.other_notes ?? "").trim(),
    });
    setIsFormDirty(signature !== formInitialSignature);
  };

  useEffect(() => {
    loadJobs();
    void loadResumeState();
  }, []);

  const tableColumns: ColumnsType<JobSummary> = useMemo(
    () => [
      {
        title: "岗位名称",
        dataIndex: "title",
        key: "title",
        width: 180,
        render: (value: string, record) => (
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => {
              void openJobDetail(record.job_id);
            }}
          >
            {value}
          </Button>
        ),
      },
      {
        title: "公司",
        dataIndex: "company",
        key: "company",
        width: 150,
        render: (value: string | null) => value || "-",
      },
      {
        title: "部门",
        dataIndex: "department",
        key: "department",
        width: 130,
        render: (value: string | null) => value || "-",
      },
      {
        title: "投递状态",
        dataIndex: "application_status",
        key: "application_status",
        width: 100,
        render: (value: string) => <Tag>{value}</Tag>,
      },
      {
        title: "状态",
        dataIndex: "status",
        key: "status",
        width: 90,
        render: (value: string) => <Tag color={value === "archived" ? "orange" : "green"}>{value}</Tag>,
      },
      {
        title: "绑定状态",
        dataIndex: "binding_summary",
        key: "binding_summary",
        width: 170,
        render: (value: JobBindingSummary) => {
          if (value.status === "bound") {
            return <Tag color="blue">{buildBindingLabel(value)}</Tag>;
          }
          return <Tag>{buildBindingLabel(value)}</Tag>;
        },
      },
      {
        title: "匹配分析",
        dataIndex: "latest_match_summary",
        key: "latest_match_summary",
        width: 140,
        render: (value: { status: string }) => <Tag>{value?.status || "match_not_generated"}</Tag>,
      },
      {
        title: "更新时间",
        dataIndex: "updated_at",
        key: "updated_at",
        width: 170,
        render: (value: string) => toDisplayDate(value),
      },
      {
        title: "操作",
        key: "actions",
        width: 160,
        fixed: "right",
        render: (_, record) => (
          <Space size="small">
            <Tooltip title="查看">
              <Button
                type="text"
                size="small"
                icon={<EyeOutlined />}
                onClick={() => {
                  void openJobDetail(record.job_id);
                }}
              />
            </Tooltip>
            <Tooltip title="编辑">
              <Button
                type="text"
                size="small"
                icon={<EditOutlined />}
                onClick={() => {
                  void openJobEdit(record.job_id);
                }}
              />
            </Tooltip>
            <Tooltip title="归档">
              <Button
                type="text"
                size="small"
                danger
                icon={<InboxOutlined />}
                loading={archivingJobId === record.job_id}
                onClick={() => {
                  void archiveJob(record);
                }}
              />
            </Tooltip>
          </Space>
        ),
      },
    ],
    [archivingJobId],
  );

  const renderBindingPanel = (job: JobDetail | null) => {
    if (job === null) {
      return null;
    }

    const summary = job.binding_summary;
    const bindingLoading = bindingMode !== "idle";
    const isBindingActionBusy = bindingMode === "binding" || bindingMode === "unbinding";

    return (
      <Card title="绑定状态">
        <Row gutter={[0, 12]}>
          <Col span={24}>
            <Typography.Text strong>当前绑定</Typography.Text>
            <div style={{ marginTop: 8 }}>
              <Tag color={summary.status === "bound" ? "green" : "default"}>
                {summary.status === "bound" ? "已绑定" : "未绑定"}
              </Tag>
              {summary.resume_title ? (
                <Typography.Text style={{ marginLeft: 8 }}>{summary.resume_title}</Typography.Text>
              ) : null}
              {summary.resume_id && summary.status === "bound" ? (
                <Typography.Text type="secondary" style={{ marginLeft: 8 }}>
                  （{summary.resume_id}）
                </Typography.Text>
              ) : null}
              {summary.bound_at ? (
                <Typography.Text type="secondary" style={{ marginLeft: 8 }}>
                  绑定于 {toDisplayDate(summary.bound_at)}
                </Typography.Text>
              ) : null}
              {summary.resume_version_ref ? (
                <Typography.Text type="secondary" style={{ marginLeft: 8 }}>
                  版本 {summary.resume_version_ref.version_id}
                </Typography.Text>
              ) : null}
            </div>
          </Col>

          {summary.status === "bound" ? (
            <Col span={24}>
              <Button
                type="default"
                danger
                loading={bindingMode === "unbinding"}
                onClick={() => {
                  void unbindResumeFromJob();
                }}
              >
                解除绑定
              </Button>
            </Col>
          ) : null}

          {summary.status !== "bound" ? (
            <Col span={24}>
              {resumeState.kind === "error" ? (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={resumeState.message} />
              ) : null}
              {resumeState.kind === "ready" ? (
                <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                  <Select
                    style={{ flex: 1 }}
                    value={selectedResumeId ?? undefined}
                    onChange={(value) => {
                      setSelectedResumeId(value);
                    }}
                    options={getResumeSelectItems()}
                    placeholder="选择可绑定简历"
                    disabled={isBindingActionBusy}
                  />
                  <Button
                    type="primary"
                    loading={bindingMode === "binding"}
                    disabled={selectedResumeId === null}
                    onClick={() => {
                      void bindResumeToJob();
                    }}
                  >
                    绑定
                  </Button>
                </div>
              ) : null}
              {resumeState.kind === "ready" && resumeState.resumes.length === 0 ? (
                <Alert
                  style={{ marginTop: 8 }}
                  type="warning"
                  showIcon
                  message="暂无可绑定简历"
                />
              ) : null}
            </Col>
          ) : null}

          <Col span={24}>
            {isBindingActionBusy ? (
              <Typography.Text type="secondary">绑定/解绑中...</Typography.Text>
            ) : null}
            {bindingError ? (
              <Alert
                message={bindingError.message}
                description={toErrorHint(bindingError)}
                type="error"
                showIcon
                style={{ marginTop: 8 }}
              />
            ) : null}
            {bindingResult ? (
              <Alert
                style={{ marginTop: 8 }}
                type="info"
                showIcon
                message={`最近一次绑定动作：${bindingResult.binding_status}（record_version=${bindingResult.record_version}）`}
              />
            ) : null}
          </Col>
        </Row>
      </Card>
    );
  };

  return (
    <AppShell>
      <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: 12 }}>
        <Space direction="vertical" size={4} style={{ width: "100%" }}>
          <Typography.Title level={4} style={{ margin: 0 }}>
            岗位 / JD 管理
          </Typography.Title>
          <Typography.Text type="secondary">
            支持岗位列表、创建 / 编辑、详情查看、归档与简历绑定联调。
          </Typography.Text>
        </Space>

        <Card>
          <Space wrap>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={openCreateForm}
              disabled={formLoading}
            >
              新增岗位
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                void loadJobs();
              }}
            >
              刷新
            </Button>
          </Space>
        </Card>

        <Card>
          {isJobsLoading ? (
            <LoadingState compact message="岗位列表加载中..." />
          ) : jobsError !== null ? (
            <ErrorState
              compact
              message="岗位列表加载失败"
              details={jobsError.message}
              description={toErrorHint(jobsError)}
              actionLabel={jobsError.actionLabel}
              onAction={() => {
                if (jobsError.kind === "unauthorized") {
                  navigate("/login", { replace: true });
                } else {
                  void loadJobs();
                }
              }}
            />
          ) : jobs.length === 0 ? (
            <EmptyState
              compact
              title="暂无岗位"
              description="当前暂无岗位记录"
              action={
                <Button type="primary" icon={<PlusOutlined />} onClick={openCreateForm}>
                  新建岗位
                </Button>
              }
            />
          ) : (
            <Table<JobSummary>
              rowKey="job_id"
              columns={tableColumns}
              dataSource={jobs}
              pagination={{ pageSize: 10, showSizeChanger: true }}
              size="small"
              scroll={{ x: 1100 }}
            />
          )}
        </Card>

        <Drawer
          title="岗位详情"
          width={680}
          open={detailOpen}
          onClose={closeDetail}
          destroyOnClose
          extra={
            selectedJob
              ? [
                  <Button
                    key="edit"
                    icon={<EditOutlined />}
                    onClick={() => {
                      void openJobEdit(selectedJob.job_id);
                    }}
                  >
                    编辑岗位
                  </Button>,
                ]
              : null
          }
        >
          {detailLoading ? (
            <LoadingState compact message="岗位详情加载中..." />
          ) : detailError !== null ? (
            <ErrorState compact message="岗位详情加载失败" details={detailError.message} description={toErrorHint(detailError)} />
          ) : selectedJob === null ? (
            <EmptyState compact title="暂无数据" description="未获取到岗位详情。" />
          ) : (
            <Space direction="vertical" size={12} style={{ width: "100%" }}>
              <Card size="small" title="基础信息">
                <List size="small">
                  <List.Item>
                    <List.Item.Meta title="岗位名称" description={selectedJob.title} />
                  </List.Item>
                  <List.Item>
                    <List.Item.Meta title="公司" description={selectedJob.company || "-"} />
                  </List.Item>
                  <List.Item>
                    <List.Item.Meta title="部门" description={selectedJob.department || "-"} />
                  </List.Item>
                  <List.Item>
                    <List.Item.Meta title="投递状态" description={selectedJob.application_status} />
                  </List.Item>
                  <List.Item>
                    <List.Item.Meta title="岗位状态" description={selectedJob.status} />
                  </List.Item>
                  <List.Item>
                    <List.Item.Meta
                      title="版本信息"
                      description={`当前版本 ${selectedJob.current_version_ref.version_id}（record_version=${selectedJob.record_version}）`}
                    />
                  </List.Item>
                  <List.Item>
                    <List.Item.Meta title="更新时间" description={toDisplayDate(selectedJob.updated_at)} />
                  </List.Item>
                  <List.Item>
                    <List.Item.Meta
                      title="匹配分析占位"
                      description={selectedJob.latest_match_summary?.status || "match_not_generated"}
                    />
                  </List.Item>
                </List>
              </Card>

              <Card size="small" title="岗位内容">
                <Space direction="vertical" style={{ width: "100%" }}>
                  <div>
                    <Typography.Text strong>岗位职责</Typography.Text>
                    <List
                      size="small"
                      dataSource={selectedJob.responsibilities}
                      renderItem={(item) => <List.Item>{item}</List.Item>}
                    />
                  </div>

                  <div>
                    <Typography.Text strong>岗位要求</Typography.Text>
                    <List
                      size="small"
                      dataSource={selectedJob.requirements}
                      renderItem={(item) => <List.Item>{item}</List.Item>}
                    />
                  </div>

                  <div>
                    <Typography.Text strong>其他说明</Typography.Text>
                    <Typography.Paragraph>{selectedJob.other_notes || "-"}</Typography.Paragraph>
                  </div>
                </Space>
              </Card>

              {renderBindingPanel(selectedJob)}
            </Space>
          )}
        </Drawer>

        <Drawer
          title={formMode === "create" ? "新增岗位" : "编辑岗位"}
          width={620}
          open={formOpen}
          onClose={requestCloseForm}
          destroyOnClose
          extra={
            <Button
              type="primary"
              icon={<CheckCircleOutlined />}
              loading={formSubmitLoading}
              disabled={formSubmitLoading || !isFormDirty}
              onClick={() => {
                void saveJob();
              }}
            >
              保存
            </Button>
          }
        >
          {formLoading ? (
            <div style={{ padding: 24, display: "grid", placeItems: "center" }}>
              <Spin />
            </div>
          ) : (
            <Space direction="vertical" size={12} style={{ width: "100%" }}>
              {formError !== null ? (
                <Alert
                  type="error"
                  message={formError.message}
                  description={toErrorHint(formError)}
                  showIcon
                />
              ) : null}

              <Form<JobFormValues> form={form} layout="vertical" onValuesChange={onFormValuesChange}>
                <Row gutter={12}>
                  <Col span={24}>
                    <Form.Item
                      label="岗位名称"
                      name="title"
                      rules={[
                        { required: true, message: "岗位名称不能为空" },
                        { max: 160, message: "岗位名称不能超过 160 个字符" },
                      ]}
                    >
                      <Input placeholder="例如：前端工程师" maxLength={160} />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item label="所属公司" name="company" rules={[{ max: 160, message: "公司名称不能超过 160 个字符" }]}>
                      <Input placeholder="例如：示例科技有限公司" maxLength={160} />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item label="所属部门" name="department" rules={[{ max: 160, message: "部门名称不能超过 160 个字符" }]}>
                      <Input placeholder="例如：研发部" maxLength={160} />
                    </Form.Item>
                  </Col>
                  <Col span={24}>
                    <Form.Item
                      label="岗位职责"
                      name="responsibilitiesText"
                      rules={[
                        { required: true, message: "至少填写 1 条岗位职责" },
                        {
                          validator: (_, value) => {
                            const list = splitList(value);
                            return list.length > 0
                              ? Promise.resolve()
                              : Promise.reject(new Error("岗位职责不能为空"));
                          },
                        },
                      ]}
                    >
                      <Input.TextArea
                        rows={TEXTAREA_ROWS}
                        placeholder="每行一条，例如：负责用户体验优化"
                      />
                    </Form.Item>
                  </Col>
                  <Col span={24}>
                    <Form.Item
                      label="岗位要求"
                      name="requirementsText"
                      rules={[
                        { required: true, message: "至少填写 1 条岗位要求" },
                        {
                          validator: (_, value) => {
                            const list = splitList(value);
                            return list.length > 0
                              ? Promise.resolve()
                              : Promise.reject(new Error("岗位要求不能为空"));
                          },
                        },
                      ]}
                    >
                      <Input.TextArea
                        rows={TEXTAREA_ROWS}
                        placeholder="每行一条，例如：精通 React"
                      />
                    </Form.Item>
                  </Col>
                  <Col span={24}>
                    <Form.Item label="其他说明" name="other_notes">
                      <Input.TextArea rows={4} placeholder="补充说明（可选）" />
                    </Form.Item>
                  </Col>
                  <Col span={24}>
                    <Form.Item label="投递状态" name="application_status">
                      <Select
                        options={[
                          { value: "draft", label: "草稿" },
                          { value: "applied", label: "已投递" },
                          { value: "interviewing", label: "进行中" },
                          { value: "closed", label: "已关闭" },
                        ]}
                      />
                    </Form.Item>
                  </Col>
                </Row>
              </Form>
            </Space>
          )}
        </Drawer>
      </div>
    </AppShell>
  );
}
