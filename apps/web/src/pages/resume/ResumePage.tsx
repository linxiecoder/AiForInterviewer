import { useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Drawer, Form, Input, Space, Table, Tag, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { CheckCircleOutlined, PlusOutlined, ReloadOutlined } from "@ant-design/icons";
import { AppShell } from "../../widgets/app-shell/AppShell";
import {
  createResume,
  fetchResumeSummaries,
  type ResumeApiState,
} from "../../entities/resume/api/resumeApi";
import type { ResumeSummary } from "../../entities/resume/model/types";
import { isApiHttpError } from "../../shared/api/errors";
import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorState } from "../../shared/ui/ErrorState";
import { LoadingState } from "../../shared/ui/LoadingState";
import { useRouteController } from "../../app/routes/router";

type ResumeFormValues = {
  title: string;
  markdown_text: string;
};

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

function toCreateErrorMessage(error: unknown): string {
  if (isApiHttpError(error)) {
    return error.safeMessage;
  }
  if (error instanceof Error) {
    return error.message || "简历创建失败";
  }
  return "简历创建失败";
}

export function ResumePage() {
  const { navigate } = useRouteController();
  const [form] = Form.useForm<ResumeFormValues>();
  const [resumeState, setResumeState] = useState<ResumeApiState>({ kind: "ready", resumes: [] });
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [formOpen, setFormOpen] = useState<boolean>(false);
  const [formSubmitLoading, setFormSubmitLoading] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  const loadResumes = async () => {
    setIsLoading(true);
    try {
      const state = await fetchResumeSummaries();
      setResumeState(state);
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

  const columns: ColumnsType<ResumeSummary> = useMemo(
    () => [
      {
        title: "简历名称",
        dataIndex: "title",
        key: "title",
        render: (_, record) => (
          <Space direction="vertical" size={0}>
            <Typography.Text strong>{getResumeTitle(record)}</Typography.Text>
            <Typography.Text type="secondary">{record.resume_id}</Typography.Text>
          </Space>
        ),
      },
      {
        title: "状态",
        dataIndex: "status",
        key: "status",
        width: 120,
        render: (value: string | null | undefined) => <Tag>{value || "active"}</Tag>,
      },
      {
        title: "当前版本",
        dataIndex: "current_version_id",
        key: "current_version_id",
        width: 160,
        render: (value: string | null | undefined, record) =>
          value || record.current_version_ref?.version_id || "-",
      },
      {
        title: "更新时间",
        dataIndex: "updated_at",
        key: "updated_at",
        width: 180,
        render: (value: string) => toDisplayDate(value),
      },
    ],
    [],
  );

  return (
    <AppShell>
      <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: 12 }}>
        <Card>
          <Space wrap style={{ width: "100%", justifyContent: "space-between" }}>
            <div>
              <Typography.Title level={4} style={{ margin: 0 }}>
                我的简历
              </Typography.Title>
              <Typography.Text type="secondary">管理当前账号可用于岗位绑定的简历。</Typography.Text>
            </div>
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
          </Space>
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
          ) : (
            <Table<ResumeSummary>
              rowKey="resume_id"
              size="small"
              columns={columns}
              dataSource={resumeState.resumes}
              pagination={{
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 条`,
              }}
            />
          )}
        </Card>

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
                <Input.TextArea
                  rows={12}
                  placeholder="粘贴 Markdown 或纯文本简历内容"
                />
              </Form.Item>
            </Form>
          </Space>
        </Drawer>
      </div>
    </AppShell>
  );
}
