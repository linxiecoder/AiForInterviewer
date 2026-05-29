import { type ReactNode, useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Descriptions, Drawer, Form, Input, Modal, Space, Table, Tag, Tooltip, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { CheckCircleOutlined, DeleteOutlined, EditOutlined, InboxOutlined, LinkOutlined, PlusOutlined, ReloadOutlined, SearchOutlined } from "@ant-design/icons";
import { AppShell } from "../../widgets/app-shell/AppShell";
import { createBinding, fetchJobs, removeBinding } from "../../entities/job/api/jobApi";
import type { JobSummary } from "../../entities/job/model/types";
import {
  createResume,
  deleteResume,
  fetchResumeDetail,
  fetchResumeSummaries,
  type ResumeApiState,
  updateResume,
} from "../../entities/resume/api/resumeApi";
import type { ResumeDetail, ResumeSummary } from "../../entities/resume/model/types";
import { isApiHttpError } from "../../shared/api/errors";
import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorState } from "../../shared/ui/ErrorState";
import { LoadingState } from "../../shared/ui/LoadingState";
import { useRouteController } from "../../app/routes/router";

type ResumeFormValues = {
  title: string;
  markdown_text: string;
};

type LinkedJobsByResumeId = Record<string, JobSummary[]>;

export const RESUME_TABLE_COLUMN_KEYS = [
  "title",
  "status",
  "score",
  "linked_job",
  "current_version_id",
  "updated_at",
  "actions",
] as const;
export const RESUME_SEARCH_FIELD_KEYS = ["title", "file_name", "resume_id", "status"] as const;
export const RESUME_ROW_ACTION_KEYS = ["link_job", "edit_resume", "archive_resume", "delete_resume"] as const;
export const RESUME_HEADER_CONTROL_ORDER = ["actions", "search"] as const;
export const RESUME_SEARCH_PLACEHOLDER = "搜索简历名称、状态";
export const RESUME_SEARCH_WIDTH = 360 as const;
export const RESUME_SEARCH_ENTER_BUTTON_KIND = "icon";
export const RESUME_TITLE_ACTION_KEY = "open_detail";
export const RESUME_DETAIL_FIELD_KEYS = [
  "title",
  "resume_id",
  "score",
  "linked_job",
  "status",
  "current_version_id",
  "updated_at",
  "markdown_text",
] as const;
export const RESUME_EDIT_FIELD_KEYS = ["title", "markdown_text"] as const;
export const RESUME_DETAIL_MARKDOWN_PREVIEW_LABEL = "简历内容";
export const RESUME_LINK_JOB_FIELD_KEYS = ["resume_id", "job_ids", "resume_job_binding_ids"] as const;
export const RESUME_LINK_JOB_EMPTY_SELECTION_ACTION = "unbind_existing_binding";
export const RESUME_LINK_JOB_SELECTION_KIND = "checkbox";
export const RESUME_LINK_JOB_CLEAR_SELECTION_CONTROL = "none";
export const RESUME_LINK_JOB_MODAL_TITLE = "关联岗位";
export const RESUME_LINK_JOB_SAVE_BUTTON_LABEL = "保存关联";

function toDisplayDate(raw: string): string {
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) {
    return raw || "-";
  }
  return date.toLocaleString();
}

function getResumeTitle(resume: ResumeSummary): string {
  return resume.title || resume.file_name || resume.resume_id;
}

export function filterResumesBySearch(resumes: readonly ResumeSummary[], rawKeyword: string): ResumeSummary[] {
  const keyword = rawKeyword.trim().toLowerCase();
  if (keyword.length === 0) {
    return [...resumes];
  }

  return resumes.filter((resume) =>
    RESUME_SEARCH_FIELD_KEYS.some((fieldKey) => {
      const value = resume[fieldKey];
      return typeof value === "string" && value.toLowerCase().includes(keyword);
    }),
  );
}

function buildLinkedJobsByResumeId(jobs: JobSummary[]): LinkedJobsByResumeId {
  return jobs.reduce<LinkedJobsByResumeId>((accumulator, job) => {
    const summary = job.binding_summary;
    if (summary.status !== "bound" || !summary.resume_id) {
      return accumulator;
    }
    accumulator[summary.resume_id] = [...(accumulator[summary.resume_id] ?? []), job];
    return accumulator;
  }, {});
}

function renderResumeScore(resume: ResumeSummary) {
  const score = resume.latest_score_summary?.display_score;
  if (typeof score === "number") {
    return (
      <Space direction="vertical" size={0}>
        <Typography.Text strong>{score}</Typography.Text>
        <Typography.Text type="secondary">/ 100</Typography.Text>
      </Space>
    );
  }
  return <Tag>待评分</Tag>;
}

function renderLinkedJobs(jobs: JobSummary[] | undefined) {
  if (!jobs || jobs.length === 0) {
    return <Typography.Text type="secondary">未关联</Typography.Text>;
  }

  const [firstJob, ...remainingJobs] = jobs;
  return (
    <Space size={4} wrap>
      <Typography.Text>{firstJob.title}</Typography.Text>
      {remainingJobs.length > 0 ? <Tag>+{remainingJobs.length}</Tag> : null}
    </Space>
  );
}

function findLinkedJobsForResume(jobs: readonly JobSummary[], resumeId: string): JobSummary[] {
  return jobs.filter((job) =>
    job.binding_summary.status === "bound"
    && job.binding_summary.resume_id === resumeId
    && job.binding_summary.resume_job_binding_id,
  );
}

function renderInlineMarkdown(text: string): ReactNode {
  const nodes: ReactNode[] = [];
  const pattern = /(\*\*([^*]+)\*\*|`([^`]+)`)/g;
  let cursor = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > cursor) {
      nodes.push(text.slice(cursor, match.index));
    }
    if (match[2]) {
      nodes.push(<strong key={`strong-${match.index}`}>{match[2]}</strong>);
    } else if (match[3]) {
      nodes.push(<Typography.Text key={`code-${match.index}`} code>{match[3]}</Typography.Text>);
    }
    cursor = match.index + match[0].length;
  }

  if (cursor < text.length) {
    nodes.push(text.slice(cursor));
  }

  return nodes.length > 0 ? nodes : text;
}

function renderMarkdownPreview(markdownText: string) {
  const source = markdownText.trim();
  if (source.length === 0) {
    return <Typography.Text type="secondary">暂无简历内容</Typography.Text>;
  }

  const blocks: ReactNode[] = [];
  let paragraphLines: string[] = [];
  let unorderedItems: string[] = [];
  let orderedItems: string[] = [];
  let codeLines: string[] | null = null;

  const flushParagraph = () => {
    if (paragraphLines.length === 0) {
      return;
    }
    blocks.push(
      <Typography.Paragraph key={`paragraph-${blocks.length}`} style={{ marginBottom: 8 }}>
        {renderInlineMarkdown(paragraphLines.join(" "))}
      </Typography.Paragraph>,
    );
    paragraphLines = [];
  };

  const flushUnorderedList = () => {
    if (unorderedItems.length === 0) {
      return;
    }
    blocks.push(
      <ul key={`ul-${blocks.length}`} style={{ margin: "0 0 10px", paddingLeft: 20 }}>
        {unorderedItems.map((item, index) => (
          <li key={`${item}-${index}`}>{renderInlineMarkdown(item)}</li>
        ))}
      </ul>,
    );
    unorderedItems = [];
  };

  const flushOrderedList = () => {
    if (orderedItems.length === 0) {
      return;
    }
    blocks.push(
      <ol key={`ol-${blocks.length}`} style={{ margin: "0 0 10px", paddingLeft: 20 }}>
        {orderedItems.map((item, index) => (
          <li key={`${item}-${index}`}>{renderInlineMarkdown(item)}</li>
        ))}
      </ol>,
    );
    orderedItems = [];
  };

  const flushTextBlocks = () => {
    flushParagraph();
    flushUnorderedList();
    flushOrderedList();
  };

  for (const line of source.split(/\r?\n/)) {
    const trimmed = line.trim();

    if (trimmed.startsWith("```")) {
      if (codeLines === null) {
        flushTextBlocks();
        codeLines = [];
      } else {
        blocks.push(
          <pre key={`code-block-${blocks.length}`} style={{ margin: "0 0 10px", padding: 12, overflowX: "auto", background: "#f5f7fb", borderRadius: 6, fontSize: 12 }}>
            <code>{codeLines.join("\n")}</code>
          </pre>,
        );
        codeLines = null;
      }
      continue;
    }

    if (codeLines !== null) {
      codeLines.push(line);
      continue;
    }

    if (trimmed.length === 0) {
      flushTextBlocks();
      continue;
    }

    const headingMatch = /^(#{1,3})\s+(.+)$/.exec(trimmed);
    if (headingMatch) {
      flushTextBlocks();
      blocks.push(
        <Typography.Title
          key={`heading-${blocks.length}`}
          level={(headingMatch[1].length + 2) as 3 | 4 | 5}
          style={{ margin: "4px 0 8px" }}
        >
          {renderInlineMarkdown(headingMatch[2])}
        </Typography.Title>,
      );
      continue;
    }

    const unorderedMatch = /^[-*]\s+(.+)$/.exec(trimmed);
    if (unorderedMatch) {
      flushParagraph();
      flushOrderedList();
      unorderedItems.push(unorderedMatch[1]);
      continue;
    }

    const orderedMatch = /^\d+\.\s+(.+)$/.exec(trimmed);
    if (orderedMatch) {
      flushParagraph();
      flushUnorderedList();
      orderedItems.push(orderedMatch[1]);
      continue;
    }

    const quoteMatch = /^>\s+(.+)$/.exec(trimmed);
    if (quoteMatch) {
      flushTextBlocks();
      blocks.push(
        <blockquote key={`quote-${blocks.length}`} style={{ margin: "0 0 10px", paddingLeft: 12, color: "#5f6f89", borderLeft: "3px solid #d6e4ff" }}>
          {renderInlineMarkdown(quoteMatch[1])}
        </blockquote>,
      );
      continue;
    }

    paragraphLines.push(trimmed);
  }

  if (codeLines !== null) {
    blocks.push(
      <pre key={`code-block-${blocks.length}`} style={{ margin: "0 0 10px", padding: 12, overflowX: "auto", background: "#f5f7fb", borderRadius: 6, fontSize: 12 }}>
        <code>{codeLines.join("\n")}</code>
      </pre>,
    );
  }
  flushTextBlocks();

  return blocks;
}

function toResumePageErrorMessage(error: unknown, fallback: string): string {
  if (isApiHttpError(error)) {
    return error.safeMessage;
  }
  if (error instanceof Error) {
    return error.message || fallback;
  }
  return fallback;
}

function toCreateErrorMessage(error: unknown): string {
  return toResumePageErrorMessage(error, "简历创建失败");
}

export function ResumePage() {
  const { navigate } = useRouteController();
  const [form] = Form.useForm<ResumeFormValues>();
  const [editForm] = Form.useForm<ResumeFormValues>();
  const [resumeState, setResumeState] = useState<ResumeApiState>({ kind: "ready", resumes: [] });
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [linkedJobsByResumeId, setLinkedJobsByResumeId] = useState<LinkedJobsByResumeId>({});
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [formOpen, setFormOpen] = useState<boolean>(false);
  const [detailResume, setDetailResume] = useState<ResumeDetail | null>(null);
  const [detailLoadingResumeId, setDetailLoadingResumeId] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [editingResume, setEditingResume] = useState<ResumeDetail | null>(null);
  const [editLoadingResumeId, setEditLoadingResumeId] = useState<string | null>(null);
  const [editSubmitLoading, setEditSubmitLoading] = useState<boolean>(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [linkingResume, setLinkingResume] = useState<ResumeSummary | null>(null);
  const [selectedJobIds, setSelectedJobIds] = useState<string[]>([]);
  const [linkJobSearchKeyword, setLinkJobSearchKeyword] = useState<string>("");
  const [linkJobListLoading, setLinkJobListLoading] = useState<boolean>(false);
  const [linkJobSubmitLoading, setLinkJobSubmitLoading] = useState<boolean>(false);
  const [linkJobError, setLinkJobError] = useState<string | null>(null);
  const [searchKeyword, setSearchKeyword] = useState<string>("");
  const [formSubmitLoading, setFormSubmitLoading] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [deletingResumeId, setDeletingResumeId] = useState<string | null>(null);

  const loadResumes = async () => {
    setIsLoading(true);
    try {
      const [state, jobItems] = await Promise.all([
        fetchResumeSummaries(),
        fetchJobs().catch(() => []),
      ]);
      setResumeState(state);
      setJobs(jobItems);
      setLinkedJobsByResumeId(buildLinkedJobsByResumeId(jobItems));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadResumes();
  }, []);

  const openCreateForm = () => {
    form.resetFields();
    setFormError(null);
    setFormOpen(true);
  };

  const openDetailDrawer = async (resume: ResumeSummary) => {
    setDetailLoadingResumeId(resume.resume_id);
    setDetailError(null);
    try {
      const detail = await fetchResumeDetail(resume.resume_id);
      setDetailResume(detail);
    } catch (error) {
      const errorMessage = toResumePageErrorMessage(error, "简历详情加载失败");
      setDetailError(errorMessage);
      message.error(errorMessage);
    } finally {
      setDetailLoadingResumeId(null);
    }
  };

  const openEditForm = async (resume: ResumeSummary) => {
    setEditLoadingResumeId(resume.resume_id);
    setEditError(null);
    try {
      const detail = await fetchResumeDetail(resume.resume_id);
      editForm.setFieldsValue({
        title: getResumeTitle(detail),
        markdown_text: detail.markdown_text,
      });
      setEditingResume(detail);
    } catch (error) {
      const errorMessage = toResumePageErrorMessage(error, "简历编辑信息加载失败");
      setEditError(errorMessage);
      message.error(errorMessage);
    } finally {
      setEditLoadingResumeId(null);
    }
  };

  const openLinkJobModal = async (resume: ResumeSummary) => {
    setLinkingResume(resume);
    setLinkJobSearchKeyword("");
    setLinkJobError(null);
    setSelectedJobIds((linkedJobsByResumeId[resume.resume_id] ?? []).map((job) => job.job_id));
    setLinkJobListLoading(true);
    try {
      const jobItems = await fetchJobs();
      setJobs(jobItems);
      setLinkedJobsByResumeId(buildLinkedJobsByResumeId(jobItems));
      setSelectedJobIds(findLinkedJobsForResume(jobItems, resume.resume_id).map((job) => job.job_id));
    } catch (error) {
      setLinkJobError(toResumePageErrorMessage(error, "岗位列表加载失败"));
    } finally {
      setLinkJobListLoading(false);
    }
  };

  const saveResume = async () => {
    let values: ResumeFormValues;
    try {
      values = await form.validateFields();
    } catch {
      return;
    }

    setFormSubmitLoading(true);
    setFormError(null);
    try {
      const response = await createResume({
        title: values.title.trim(),
        markdown_text: values.markdown_text.trim(),
      });
      message.success(`简历「${getResumeTitle(response)}」创建成功。`);
      await loadResumes();
      setFormOpen(false);
    } catch (error) {
      setFormError(toCreateErrorMessage(error));
    } finally {
      setFormSubmitLoading(false);
    }
  };

  const saveEditedResume = async () => {
    if (editingResume === null) {
      return;
    }

    let values: ResumeFormValues;
    try {
      values = await editForm.validateFields();
    } catch {
      return;
    }

    setEditSubmitLoading(true);
    setEditError(null);
    try {
      const updated = await updateResume(editingResume.resume_id, {
        title: values.title.trim(),
        markdown_text: values.markdown_text.trim(),
        base_version_ref: editingResume.current_version_ref,
      });
      message.success(`简历「${getResumeTitle(updated)}」更新成功。`);
      await loadResumes();
      setEditingResume(null);
    } catch (error) {
      setEditError(toResumePageErrorMessage(error, "简历更新失败"));
    } finally {
      setEditSubmitLoading(false);
    }
  };

  const confirmDeleteResume = (resume: ResumeSummary) => {
    Modal.confirm({
      title: `确认删除简历「${getResumeTitle(resume)}」？`,
      content: "删除后该简历将从列表中移除，数据库记录仅标记为 deleted，不会被物理删除。",
      okText: "删除",
      cancelText: "取消",
      okButtonProps: { danger: true },
      onOk: async () => {
        setDeletingResumeId(resume.resume_id);
        try {
          await deleteResume(resume.resume_id);
          message.success(`简历「${getResumeTitle(resume)}」已删除。`);
          if (detailResume?.resume_id === resume.resume_id) {
            setDetailResume(null);
          }
          if (editingResume?.resume_id === resume.resume_id) {
            setEditingResume(null);
          }
          if (linkingResume?.resume_id === resume.resume_id) {
            setLinkingResume(null);
          }
          await loadResumes();
        } catch (error) {
          message.error(toResumePageErrorMessage(error, "简历删除失败"));
        } finally {
          setDeletingResumeId(null);
        }
      },
    });
  };

  const saveLinkedJob = async () => {
    if (linkingResume === null) {
      return;
    }

    setLinkJobSubmitLoading(true);
    setLinkJobError(null);
    try {
      const activeLinkedJobs = findLinkedJobsForResume(jobs, linkingResume.resume_id);
      const selectedJobIdSet = new Set(selectedJobIds);
      const activeJobIdSet = new Set(activeLinkedJobs.map((job) => job.job_id));
      const bindingsToRemove = activeLinkedJobs
        .filter((job) => !selectedJobIdSet.has(job.job_id))
        .map((job) => job.binding_summary.resume_job_binding_id)
        .filter((bindingId): bindingId is string => typeof bindingId === "string");
      const jobIdsToBind = selectedJobIds.filter((jobId) => !activeJobIdSet.has(jobId));

      await Promise.all([
        ...bindingsToRemove.map((bindingId) => removeBinding(bindingId)),
        ...jobIdsToBind.map((jobId) =>
          createBinding({
            resume_id: linkingResume.resume_id,
            job_id: jobId,
          }),
        ),
      ]);

      const actionSummary = [
        jobIdsToBind.length > 0 ? `新增 ${jobIdsToBind.length} 个关联` : null,
        bindingsToRemove.length > 0 ? `取消 ${bindingsToRemove.length} 个关联` : null,
      ].filter(Boolean).join("，") || "关联未变化";
      message.success(`简历「${getResumeTitle(linkingResume)}」${actionSummary}。`);
      await loadResumes();
      setLinkingResume(null);
      setSelectedJobIds([]);
    } catch (error) {
      setLinkJobError(toResumePageErrorMessage(error, "关联岗位失败"));
    } finally {
      setLinkJobSubmitLoading(false);
    }
  };

  const filteredResumes = useMemo(
    () =>
      resumeState.kind === "ready"
        ? filterResumesBySearch(resumeState.resumes, searchKeyword)
        : [],
    [resumeState, searchKeyword],
  );

  const filteredLinkJobs = useMemo(() => {
    const keyword = linkJobSearchKeyword.trim().toLowerCase();
    if (!keyword) {
      return jobs;
    }
    return jobs.filter((job) =>
      [
        job.title,
        job.company,
        job.department,
        job.application_status,
        job.status,
        job.binding_summary.resume_title,
        job.binding_summary.resume_id,
      ].some((value) => (value ?? "").toLowerCase().includes(keyword)),
    );
  }, [jobs, linkJobSearchKeyword]);

  const activeLinkedJobs = linkingResume === null ? [] : findLinkedJobsForResume(jobs, linkingResume.resume_id);

  const columns: ColumnsType<ResumeSummary> = [
    {
      title: "简历名称",
      dataIndex: "title",
      key: "title",
      width: 190,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Button
            type="link"
            size="small"
            data-resume-action={RESUME_TITLE_ACTION_KEY}
            loading={detailLoadingResumeId === record.resume_id}
            style={{ height: "auto", padding: 0, fontWeight: 600, whiteSpace: "normal", textAlign: "left" }}
            onClick={() => {
              void openDetailDrawer(record);
            }}
          >
            {getResumeTitle(record)}
          </Button>
          <Typography.Text type="secondary">{record.resume_id}</Typography.Text>
        </Space>
      ),
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 90,
      render: (value: string | null | undefined) => <Tag>{value || "active"}</Tag>,
    },
    {
      title: "简历分数",
      dataIndex: "latest_score_summary",
      key: "score",
      width: 110,
      render: (_, record) => renderResumeScore(record),
    },
    {
      title: "关联岗位",
      key: "linked_job",
      width: 180,
      render: (_, record) => renderLinkedJobs(linkedJobsByResumeId[record.resume_id]),
    },
    {
      title: "当前版本",
      dataIndex: "current_version_id",
      key: "current_version_id",
      width: 220,
      ellipsis: true,
      render: (value: string | null | undefined, record) =>
        value || record.current_version_ref?.version_id || "-",
    },
    {
      title: "更新时间",
      dataIndex: "updated_at",
      key: "updated_at",
      width: 160,
      render: (value: string) => toDisplayDate(value),
    },
    {
      title: "操作",
      key: "actions",
      width: 168,
      render: (_, record) => (
        <Space size={4}>
          <Tooltip title="关联岗位">
            <Button
              type="text"
              size="small"
              icon={<LinkOutlined />}
              onClick={() => {
                void openLinkJobModal(record);
              }}
            />
          </Tooltip>
          <Tooltip title="编辑简历">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              loading={editLoadingResumeId === record.resume_id}
              onClick={() => {
                void openEditForm(record);
              }}
            />
          </Tooltip>
          <Tooltip title="归档简历">
            <Button
              type="text"
              size="small"
              danger
              icon={<InboxOutlined />}
              onClick={() => {
                message.warning(`简历「${getResumeTitle(record)}」归档能力待接入。`);
              }}
            />
          </Tooltip>
          <Tooltip title="删除简历">
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              loading={deletingResumeId === record.resume_id}
              aria-label="删除简历"
              onClick={() => {
                confirmDeleteResume(record);
              }}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  const linkJobColumns: ColumnsType<JobSummary> = [
    {
      title: "岗位名称",
      dataIndex: "title",
      key: "title",
      render: (value: string) => <Typography.Text strong>{value}</Typography.Text>,
    },
    {
      title: "公司",
      dataIndex: "company",
      key: "company",
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
      title: "当前关联",
      dataIndex: "binding_summary",
      key: "binding_summary",
      width: 190,
      render: (_, record) => {
        const summary = record.binding_summary;
        if (summary.status !== "bound") {
          return <Tag>未关联</Tag>;
        }
        const isCurrentResume = summary.resume_id === linkingResume?.resume_id;
        return (
          <Tag color={isCurrentResume ? "green" : "blue"}>
            {isCurrentResume ? "已关联当前简历" : summary.resume_title || summary.resume_id || "已关联"}
          </Tag>
        );
      },
    },
  ];

  return (
    <AppShell>
      <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: 12 }}>
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
              <Button type="primary" icon={<PlusOutlined />} onClick={openCreateForm}>
                新增简历
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => {
                  void loadResumes();
                }}
              >
                刷新
              </Button>
            </Space>
            <Input.Search
              allowClear
              enterButton={<SearchOutlined aria-label="搜索" />}
              value={searchKeyword}
              onChange={(event) => {
                setSearchKeyword(event.target.value);
              }}
              onSearch={(value) => {
                setSearchKeyword(value);
              }}
              placeholder={RESUME_SEARCH_PLACEHOLDER}
              style={{ width: RESUME_SEARCH_WIDTH, maxWidth: "100%", marginLeft: "auto" }}
            />
          </div>
        </Card>

        <Card>
          {isLoading ? (
            <LoadingState compact message="简历列表加载中..." />
          ) : resumeState.kind === "error" ? (
            <ErrorState
              compact
              message="简历列表加载失败"
              details={resumeState.message}
              actionLabel={resumeState.status === 401 ? "前往登录" : "重试"}
              onAction={() => {
                if (resumeState.status === 401) {
                  navigate("/login", { replace: true });
                  return;
                }
                void loadResumes();
              }}
            />
          ) : resumeState.resumes.length === 0 ? (
            <EmptyState
              compact
              title="暂无简历"
              description="当前暂无可用于岗位绑定的简历"
              action={
                <Button type="primary" icon={<PlusOutlined />} onClick={openCreateForm}>
                  新建简历
                </Button>
              }
            />
          ) : filteredResumes.length === 0 ? (
            <EmptyState
              compact
              title="未找到匹配简历"
              description="调整简历名称或状态关键词后重试"
            />
          ) : (
            <Table<ResumeSummary>
              rowKey="resume_id"
              size="small"
              columns={columns}
              dataSource={filteredResumes}
              scroll={{ x: "max-content" }}
              pagination={{
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 条`,
              }}
            />
          )}
        </Card>

        <Modal
          title={RESUME_LINK_JOB_MODAL_TITLE}
          open={linkingResume !== null}
          width={760}
          okText={RESUME_LINK_JOB_SAVE_BUTTON_LABEL}
          cancelText="取消"
          confirmLoading={linkJobSubmitLoading}
          okButtonProps={{
            disabled: (selectedJobIds.length === 0 && activeLinkedJobs.length === 0) || linkJobSubmitLoading,
          }}
          onOk={() => {
            void saveLinkedJob();
          }}
          onCancel={() => {
            setLinkingResume(null);
            setSelectedJobIds([]);
            setLinkJobError(null);
          }}
          destroyOnHidden
        >
          <Space direction="vertical" size={12} style={{ width: "100%" }}>
            {linkingResume !== null ? (
              <Typography.Text type="secondary">
                正在为简历「{getResumeTitle(linkingResume)}」选择关联岗位
              </Typography.Text>
            ) : null}
            {activeLinkedJobs.length > 0 ? (
              <Alert
                type="info"
                showIcon
                message={`当前已关联：${activeLinkedJobs.map((job) => job.title).join("、")}`}
                description="取消勾选后点击保存关联，将解除对应岗位关联。"
              />
            ) : null}
            {linkJobError !== null ? <Alert type="error" showIcon message={linkJobError} /> : null}
            <Input.Search
              allowClear
              placeholder="搜索岗位名称、公司、状态"
              value={linkJobSearchKeyword}
              onChange={(event) => {
                setLinkJobSearchKeyword(event.target.value);
              }}
              onSearch={(value) => {
                setLinkJobSearchKeyword(value);
              }}
            />
            <Table<JobSummary>
              rowKey="job_id"
              size="small"
              loading={linkJobListLoading}
              columns={linkJobColumns}
              dataSource={filteredLinkJobs}
              pagination={{ pageSize: 5, showSizeChanger: false }}
              rowSelection={{
                type: "checkbox",
                selectedRowKeys: selectedJobIds,
                onChange: (selectedRowKeys) => {
                  setSelectedJobIds(selectedRowKeys.map(String));
                },
              }}
            />
          </Space>
        </Modal>

        <Drawer
          title="简历详情"
          width={520}
          open={detailResume !== null}
          onClose={() => {
            setDetailResume(null);
            setDetailError(null);
          }}
          destroyOnClose
        >
          {detailResume !== null ? (
            <Space direction="vertical" size={16} style={{ width: "100%" }}>
              {detailError !== null ? <Alert type="error" message={detailError} showIcon /> : null}
              <Descriptions column={1} size="small" bordered>
                <Descriptions.Item label="简历名称">{getResumeTitle(detailResume)}</Descriptions.Item>
                <Descriptions.Item label="简历 ID">{detailResume.resume_id}</Descriptions.Item>
                <Descriptions.Item label="简历分数">{renderResumeScore(detailResume)}</Descriptions.Item>
                <Descriptions.Item label="关联岗位">
                  {renderLinkedJobs(linkedJobsByResumeId[detailResume.resume_id])}
                </Descriptions.Item>
                <Descriptions.Item label="状态">{detailResume.status || "active"}</Descriptions.Item>
                <Descriptions.Item label="当前版本">
                  {detailResume.current_version_id || detailResume.current_version_ref?.version_id || "-"}
                </Descriptions.Item>
                <Descriptions.Item label="更新时间">{toDisplayDate(detailResume.updated_at)}</Descriptions.Item>
              </Descriptions>
              <section>
                <Typography.Title level={5} style={{ marginTop: 0 }}>
                  {RESUME_DETAIL_MARKDOWN_PREVIEW_LABEL}
                </Typography.Title>
                <div
                  style={{
                    maxHeight: 360,
                    overflow: "auto",
                    padding: 16,
                    border: "1px solid #e7edf6",
                    borderRadius: 6,
                    background: "#fbfcff",
                  }}
                >
                  {renderMarkdownPreview(detailResume.markdown_text ?? "")}
                </div>
              </section>
            </Space>
          ) : null}
        </Drawer>

        <Drawer
          title="编辑简历"
          width={620}
          open={editingResume !== null}
          onClose={() => {
            setEditingResume(null);
            setEditError(null);
          }}
          destroyOnClose
          extra={
            <Button
              type="primary"
              icon={<CheckCircleOutlined />}
              loading={editSubmitLoading}
              disabled={editSubmitLoading}
              onClick={() => {
                void saveEditedResume();
              }}
            >
              保存
            </Button>
          }
        >
          <Space direction="vertical" size={12} style={{ width: "100%" }}>
            {editError !== null ? <Alert type="error" message={editError} showIcon /> : null}
            <Form<ResumeFormValues> form={editForm} layout="vertical">
              <Form.Item
                label="简历名称"
                name="title"
                rules={[
                  { required: true, message: "简历名称不能为空" },
                  { max: 160, message: "简历名称不能超过 160 个字符" },
                ]}
              >
                <Input placeholder="例如：前端工程师简历" maxLength={160} />
              </Form.Item>
              <Form.Item
                label="简历正文"
                name="markdown_text"
                rules={[
                  { required: true, message: "简历正文不能为空" },
                  {
                    validator: (_, value) => {
                      return typeof value === "string" && value.trim().length > 0
                        ? Promise.resolve()
                        : Promise.reject(new Error("简历正文不能为空"));
                    },
                  },
                ]}
              >
                <Input.TextArea rows={12} placeholder="粘贴 Markdown 或纯文本简历内容" />
              </Form.Item>
            </Form>
          </Space>
        </Drawer>

        <Drawer
          title="新增简历"
          width={620}
          open={formOpen}
          onClose={() => {
            setFormOpen(false);
          }}
          destroyOnClose
          extra={
            <Button
              type="primary"
              icon={<CheckCircleOutlined />}
              loading={formSubmitLoading}
              disabled={formSubmitLoading}
              onClick={() => {
                void saveResume();
              }}
            >
              保存
            </Button>
          }
        >
          <Space direction="vertical" size={12} style={{ width: "100%" }}>
            {formError !== null ? <Alert type="error" message={formError} showIcon /> : null}
            <Form<ResumeFormValues> form={form} layout="vertical">
              <Form.Item
                label="简历名称"
                name="title"
                rules={[
                  { required: true, message: "简历名称不能为空" },
                  { max: 160, message: "简历名称不能超过 160 个字符" },
                ]}
              >
                <Input placeholder="例如：前端工程师简历" maxLength={160} />
              </Form.Item>
              <Form.Item
                label="简历正文"
                name="markdown_text"
                rules={[
                  { required: true, message: "简历正文不能为空" },
                  {
                    validator: (_, value) => {
                      return typeof value === "string" && value.trim().length > 0
                        ? Promise.resolve()
                        : Promise.reject(new Error("简历正文不能为空"));
                    },
                  },
                ]}
              >
                <Input.TextArea rows={12} placeholder="粘贴 Markdown 或纯文本简历内容" />
              </Form.Item>
            </Form>
          </Space>
        </Drawer>
      </div>
    </AppShell>
  );
}
