import { ReloadOutlined, PlusOutlined } from "@ant-design/icons";
import { Button, Card, Space, Table, Tag, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useMemo, useState } from "react";
import { useRouteController } from "../../app/routes/router";
import { fetchPolishSessions } from "../../entities/polish/api/polishApi";
import type { PolishSessionSummary } from "../../entities/polish/model/types";
import { isApiHttpError } from "../../shared/api/errors";
import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorState } from "../../shared/ui/ErrorState";
import { LoadingState } from "../../shared/ui/LoadingState";
import { AppShell } from "../../widgets/app-shell/AppShell";

type InterviewListError = {
  message: string;
  details: string;
  unauthorized: boolean;
};

function toDisplayDate(raw: string): string {
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) {
    return raw;
  }
  return date.toLocaleString();
}

function toModeLabel(mode: string): string {
  if (mode === "polish") {
    return "打磨模式";
  }
  return mode;
}

function parseListError(error: unknown): InterviewListError {
  if (isApiHttpError(error)) {
    if (error.status === 401) {
      return {
        message: "请先登录后查看模拟面试列表",
        details: "当前会话已过期或尚未登录。",
        unauthorized: true,
      };
    }
    return {
      message: "模拟面试列表加载失败",
      details: error.safeMessage || "服务端返回异常，请稍后重试。",
      unauthorized: false,
    };
  }
  if (error instanceof Error) {
    return {
      message: "模拟面试列表加载失败",
      details: error.message || "网络请求异常，请稍后重试。",
      unauthorized: false,
    };
  }
  return {
    message: "模拟面试列表加载失败",
    details: "未知错误，请稍后重试。",
    unauthorized: false,
  };
}

export function InterviewPage() {
  const { navigate } = useRouteController();
  const [sessions, setSessions] = useState<PolishSessionSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<InterviewListError | null>(null);

  const loadSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await fetchPolishSessions();
      setSessions(list);
    } catch (loadError) {
      setError(parseListError(loadError));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadSessions();
  }, []);

  const columns: ColumnsType<PolishSessionSummary> = useMemo(
    () => [
      {
        title: "名称",
        dataIndex: "title",
        key: "title",
        width: 220,
        render: (value: string) => <Typography.Text strong>{value}</Typography.Text>,
      },
      {
        title: "模式",
        dataIndex: "mode",
        key: "mode",
        width: 110,
        render: (value: string) => <Tag color="blue">{toModeLabel(value)}</Tag>,
      },
      {
        title: "状态",
        dataIndex: "status",
        key: "status",
        width: 110,
        render: (value: string) => <Tag color={value === "running" ? "green" : "default"}>{value}</Tag>,
      },
      {
        title: "绑定关系",
        dataIndex: "resume_job_binding_id",
        key: "resume_job_binding_id",
        width: 180,
        render: (value: string) => <Typography.Text code>{value}</Typography.Text>,
      },
      {
        title: "主题",
        key: "topic",
        width: 180,
        render: (_, record) => (
          <Space size={4} wrap>
            {record.topic_id ? <Tag>{record.topic_id}</Tag> : <Tag>未选择</Tag>}
            {record.subtopic_id ? <Tag>{record.subtopic_id}</Tag> : null}
          </Space>
        ),
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
      <Space direction="vertical" size={16} style={{ width: "100%" }}>
        <Card>
          <Space wrap style={{ width: "100%", justifyContent: "space-between" }}>
            <div>
              <Typography.Title level={4} style={{ marginBottom: 4 }}>
                模拟面试
              </Typography.Title>
              <Typography.Text type="secondary">
                查看当前账号下的打磨模式会话记录。
              </Typography.Text>
            </div>
            <Space wrap>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => {
                  void loadSessions();
                }}
              >
                刷新
              </Button>
              <Button type="primary" icon={<PlusOutlined />} disabled>
                发起模拟面试
              </Button>
            </Space>
          </Space>
        </Card>

        <Card>
          {loading ? (
            <LoadingState compact message="模拟面试列表加载中..." />
          ) : error !== null ? (
            <ErrorState
              compact
              message={error.message}
              details={error.details}
              actionLabel={error.unauthorized ? "前往登录" : "重试"}
              onAction={() => {
                if (error.unauthorized) {
                  navigate("/login", { replace: true });
                } else {
                  void loadSessions();
                }
              }}
            />
          ) : sessions.length === 0 ? (
            <EmptyState
              compact
              title="暂无模拟面试记录"
              description="当前账号下还没有打磨模式会话。"
              reason="后续 F6 子任务会继续接入发起模拟面试和面试台流程。"
            />
          ) : (
            <Table<PolishSessionSummary>
              rowKey="id"
              columns={columns}
              dataSource={sessions}
              pagination={{
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 条`,
              }}
              size="small"
              scroll={{ x: 980 }}
            />
          )}
        </Card>
      </Space>
    </AppShell>
  );
}
