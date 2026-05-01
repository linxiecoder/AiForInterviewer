import { Alert, Button, Card, Col, Descriptions, Empty, List, Row, Space, Tag, Typography } from "antd";

import { workbenchHomeText } from "../appContent.js";

const { Paragraph, Text, Title } = Typography;

export function WorkbenchHomePage() {
  return (
    <main className="app-shell workbench-home-shell">
      <section className="workspace-header" aria-labelledby="workbench-home-title">
        <div>
          <Text className="eyebrow">{workbenchHomeText.header.eyebrow}</Text>
          <Title level={1} id="workbench-home-title">
            {workbenchHomeText.header.title}
          </Title>
          <Paragraph className="header-copy">{workbenchHomeText.header.copy}</Paragraph>
        </div>
        <div className="status-group" aria-label="R1 工作台状态">
          {workbenchHomeText.statusTags.map((tag) => (
            <Tag className="workbench-status-tag" color={statusTagColor(tag)} key={tag}>
              {tag}
            </Tag>
          ))}
        </div>
      </section>

      <section className="home-section" id="launch-entry" aria-labelledby="home-actions-title">
        <div className="home-section-heading">
          <Title level={2} id="home-actions-title">
            主操作区
          </Title>
          <Text type="secondary">围绕发起、历史、岗位、简历和知识库组织 R1 主链路。</Text>
        </div>
        <Row gutter={[16, 16]}>
          {workbenchHomeText.primaryActions.map((action) => (
            <Col xs={24} md={12} xl={8} key={action.title}>
              <Card className="home-action-card" variant="outlined">
                <Space direction="vertical" size={10}>
                  <div className="home-card-title-row">
                    <Text strong>{action.title}</Text>
                    <Tag color="blue">{action.status}</Tag>
                  </div>
                  <Paragraph>{action.description}</Paragraph>
                  <Button href={action.href} type={action.title === "发起模拟面试" ? "primary" : "default"}>
                    进入
                  </Button>
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      </section>

      <section className="home-section" id="recent-interviews" aria-labelledby="recent-title">
        <div className="home-section-heading">
          <Title level={2} id="recent-title">
            最近记录
          </Title>
          <Text type="secondary">示例记录用于保护从首页进入可信详情页的真实路径。</Text>
        </div>
        <List
          className="home-record-list"
          dataSource={[...workbenchHomeText.recentInterviews]}
          locale={{ emptyText: <Empty description="没有历史模拟记录，先从发起入口开始。" /> }}
          renderItem={(record) => (
            <List.Item
              actions={[
                <Button href={record.href} key="detail" type="link">
                  查看可信详情
                </Button>,
              ]}
            >
              <List.Item.Meta
                title={
                  <div className="home-card-title-row">
                    <Text strong>{record.title}</Text>
                    <Tag color="success">score {record.score}</Tag>
                    <Tag color="processing">{record.status}</Tag>
                  </div>
                }
                description={
                  <div className="home-record-detail">
                    <Text>{record.description}</Text>
                    <Text type="secondary">
                      session: {record.sessionId} / owner: {record.ownerId} / updated:{" "}
                      {record.updatedAt}
                    </Text>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </section>

      <section
        className="home-section"
        id="trusted-capabilities"
        aria-labelledby="capability-title"
      >
        <div className="home-section-heading">
          <Title level={2} id="capability-title">
            可信能力摘要
          </Title>
          <Text type="secondary">R1 详情页已有 E2E 保护，首页只暴露能力入口和状态摘要。</Text>
        </div>
        <Row gutter={[16, 16]}>
          {workbenchHomeText.capabilitySummary.map((capability) => (
            <Col xs={24} md={12} xl={8} key={capability.title}>
              <Card className="home-capability-card" title={capability.title} variant="outlined">
                <Paragraph>{capability.description}</Paragraph>
                <div className="trusted-tag-row">
                  {capability.tags.map((tag) => (
                    <Tag color={statusTagColor(tag)} key={tag}>
                      {tag}
                    </Tag>
                  ))}
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </section>

      <section
        className="home-section home-overview-section"
        id="workbench-entities"
        aria-labelledby="entity-title"
      >
        <div>
          <div className="home-section-heading compact-heading">
            <Title level={2} id="entity-title">
              工作台对象概览
            </Title>
            <Text type="secondary">对象关系沿用 Workbench MVP 设计，不在本页面新增后端能力。</Text>
          </div>
          <Descriptions
            className="trusted-descriptions"
            column={1}
            bordered
            items={workbenchHomeText.entitySummary.map((item) => ({
              key: item.label,
              label: item.label,
              children: item.value,
            }))}
          />
        </div>

        <div className="home-risk-stack">
          <Alert
            message="旧记录无 trace"
            description="历史记录可能缺少 trace_summary、评分维度或导出快照，详情页会展示稳定空态。"
            type="info"
            showIcon
          />
          <Alert
            message="RAG degraded / evidence missing"
            description="RAG 无结果、索引失败或权限过滤为空时，面试可继续，但复盘需要标注 evidence gap。"
            type="warning"
            showIcon
          />
          <Alert
            message="敏感字段保护"
            description="首页只展示 session、owner、状态和摘要，不展示 prompt、raw LLM response、secret 或私有存储路径。"
            type="success"
            showIcon
          />
        </div>
      </section>
    </main>
  );
}

function statusTagColor(tag: string): string {
  if (tag === "failed" || tag.includes("gap")) {
    return "warning";
  }
  if (tag === "PostgreSQL" || tag === "traceability" || tag === "E2E protected") {
    return "success";
  }
  if (tag === "RAG citation" || tag === "0-100 scoring") {
    return "blue";
  }
  if (tag === "retryable" || tag === "degraded") {
    return "processing";
  }
  return "geekblue";
}
