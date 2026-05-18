export type OverviewMetric = {
  key: string;
  title: string;
  value: number | string;
  hint: string;
  trend: string;
};

export type PriorityTone = "urgent" | "important" | "normal";

export type TodoItem = {
  key: string;
  title: string;
  count: number;
  priority: PriorityTone;
  description: string;
  actionLabel: string;
};

export type ActivityStatus = {
  label: string;
  tone: "default" | "processing" | "success" | "warning" | "error";
};

export type ActivityItem = {
  title: string;
  status: ActivityStatus;
  description: string;
  time: string;
};

export const OVERVIEW_METRICS: OverviewMetric[] = [
  {
    key: "resume",
    title: "简历管理",
    value: 8,
    hint: "待完善 3 份",
    trend: "— 0",
  },
  {
    key: "jobs",
    title: "目标岗位",
    value: 24,
    hint: "待投递 12 个",
    trend: "↗ +6",
  },
  {
    key: "progress",
    title: "投递进度",
    value: 45,
    hint: "面试中 7 个",
    trend: "↗ +8",
  },
  {
    key: "mock",
    title: "模拟面试",
    value: 5,
    hint: "待练习场景",
    trend: "↘ -2",
  },
];

export const TODO_ITEMS: TodoItem[] = [
  {
    key: "todo-resume",
    title: "待完善简历",
    count: 3,
    priority: "urgent",
    description: "产品经理简历缺少项目经历量化数据，前端开发简历缺少技术栈说明",
    actionLabel: "去完善 →",
  },
  {
    key: "todo-apply",
    title: "待投递岗位",
    count: 12,
    priority: "urgent",
    description: "12 个高匹配岗位等待投递，包括字节跳动、腾讯等公司",
    actionLabel: "去投递 →",
  },
  {
    key: "todo-interview",
    title: "待模拟面试",
    count: 5,
    priority: "important",
    description: "字节跳动产品经理岗位、阿里前端开发岗位等 5 个岗位待练习",
    actionLabel: "开始练习 →",
  },
  {
    key: "todo-review",
    title: "待复盘面试",
    count: 3,
    priority: "normal",
    description: "3 场模拟面试已完成，等待查看表现分析和改进建议",
    actionLabel: "查看复盘 →",
  },
];

export const ACTIVITY_ITEMS: ActivityItem[] = [
  {
    title: "新增简历",
    status: { label: "新建", tone: "success" },
    description: "前端开发简历 · 已完成基础信息填写",
    time: "5分钟前",
  },
  {
    title: "模拟面试完成",
    status: { label: "待复盘", tone: "processing" },
    description: "产品经理简历 · 字节跳动产品经理岗位 · 待复盘",
    time: "1小时前",
  },
  {
    title: "投递成功",
    status: { label: "已投递", tone: "default" },
    description: "前端开发简历 · 腾讯前端工程师岗位 · 已投递",
    time: "2小时前",
  },
  {
    title: "简历完善",
    status: { label: "已更新", tone: "warning" },
    description: "产品经理简历 · 更新项目经历和技能描述",
    time: "昨天",
  },
  {
    title: "模拟面试完成",
    status: { label: "待复盘", tone: "processing" },
    description: "前端开发简历 · 阿里前端岗位 · 待复盘",
    time: "昨天",
  },
  {
    title: "新增简历",
    status: { label: "新建", tone: "success" },
    description: "UI 设计师简历 · 已完成基础信息填写",
    time: "2天前",
  },
  {
    title: "投递成功",
    status: { label: "已投递", tone: "default" },
    description: "产品经理简历 · 美团产品经理岗位 · 已投递",
    time: "2天前",
  },
  {
    title: "简历完善",
    status: { label: "已更新", tone: "warning" },
    description: "前端开发简历 · 补充项目案例和技术细节",
    time: "3天前",
  },
];

export const EMPTY_STATE_SECTIONS: string[] = [
  "资料不足：请先完善用户资料",
  "未完成真实登录/权限验证：当前为结构对齐示例",
  "活动与历史仅为占位数据",
];
