export type AppShellIconKey =
  | "home"
  | "resume"
  | "target"
  | "interview"
  | "review"
  | "knowledge"
  | "growth";

export type AppShellNavItem = {
  key: string;
  label: string;
  icon: AppShellIconKey;
  path: string;
  disabled: boolean;
  disabledReason: string;
};

export const APP_SHELL_NAV_ITEMS: AppShellNavItem[] = [
  {
    key: "dashboard",
    label: "工作台",
    icon: "home",
    path: "/dashboard",
    disabled: false,
    disabledReason: "首页可进入",
  },
  {
    key: "resume",
    label: "我的简历",
    icon: "resume",
    path: "/resume",
    disabled: true,
    disabledReason: "占位：简历模块待联调",
  },
  {
    key: "job",
    label: "目标岗位",
    icon: "target",
    path: "/job",
    disabled: true,
    disabledReason: "占位：岗位模块待联调",
  },
  {
    key: "interview",
    label: "模拟面试",
    icon: "interview",
    path: "/interview",
    disabled: true,
    disabledReason: "占位：模拟面试模块待联调",
  },
  {
    key: "review",
    label: "面试复盘",
    icon: "review",
    path: "/review",
    disabled: true,
    disabledReason: "占位：复盘模块待联调",
  },
  {
    key: "asset",
    label: "学习资料",
    icon: "knowledge",
    path: "/asset",
    disabled: true,
    disabledReason: "占位：学习资料待联调",
  },
  {
    key: "training",
    label: "能力提升",
    icon: "growth",
    path: "/training",
    disabled: true,
    disabledReason: "占位：能力提升待联调",
  },
];

export const TOPBAR_SEARCH_PLACEHOLDER = "搜索简历、岗位、面试记录...";
