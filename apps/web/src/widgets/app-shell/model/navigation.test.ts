import type { RoutePath } from "../../../app/routes/router";
import { APP_SIDEBAR_COLLAPSE_CONFIG, getPersistedSidebarCollapsed } from "../Sidebar";
import { APP_SHELL_NAV_ITEMS, getActiveNavKey } from "./navigation";

type Equal<Actual, Expected> =
  (<Value>() => Value extends Actual ? 1 : 2) extends
  (<Value>() => Value extends Expected ? 1 : 2)
    ? true
    : false;

type Expect<Condition extends true> = Condition;

type NavItem = (typeof APP_SHELL_NAV_ITEMS)[number];
type ResumeNavItem = Extract<NavItem, { key: "resume" }>;
type InterviewNavItem = Extract<NavItem, { key: "interview" }>;

type ResumeRouteIsRegistered = Expect<Equal<Extract<RoutePath, "/resume">, "/resume">>;
type ResumeNavPathIsResume = Expect<Equal<ResumeNavItem["path"], "/resume">>;
type ResumeNavIsEnabled = Expect<Equal<ResumeNavItem["disabled"], false>>;
type InterviewRouteIsRegistered = Expect<Equal<Extract<RoutePath, "/interview">, "/interview">>;
type InterviewWorkbenchRouteIsRegistered = Expect<Equal<Extract<RoutePath, `/interview/${string}`>, `/interview/${string}`>>;
type InterviewNavPathIsInterview = Expect<Equal<InterviewNavItem["path"], "/interview">>;
type InterviewNavIsEnabled = Expect<Equal<InterviewNavItem["disabled"], false>>;
type SidebarExpandedWidthIsStable = Expect<Equal<typeof APP_SIDEBAR_COLLAPSE_CONFIG.expandedWidth, 240>>;
type SidebarCollapsedWidthIsIconOnly = Expect<Equal<typeof APP_SIDEBAR_COLLAPSE_CONFIG.collapsedWidth, 72>>;
type SidebarHoverLabelUsesMenuTitle = Expect<Equal<typeof APP_SIDEBAR_COLLAPSE_CONFIG.hoverLabel, "menu_item_title">>;
type SidebarCollapsePersistsLocally = Expect<Equal<typeof APP_SIDEBAR_COLLAPSE_CONFIG.persistence, "local_storage">>;
type SidebarCollapseStorageKeyIsStable = Expect<Equal<typeof APP_SIDEBAR_COLLAPSE_CONFIG.storageKey, "aifi:app-shell:sidebar-collapsed">>;
type SidebarCollapsedItemHeightMatchesExpanded = Expect<Equal<typeof APP_SIDEBAR_COLLAPSE_CONFIG.menuItemHeight, 40>>;
type SidebarPersistedReaderReturnsBoolean = Expect<Equal<ReturnType<typeof getPersistedSidebarCollapsed>, boolean>>;

const interviewListActiveKey = getActiveNavKey("/interview");
const interviewWorkbenchActiveKey = getActiveNavKey("/interview/ses_001");

type InterviewListKeepsNavActive = Expect<Equal<typeof interviewListActiveKey, "interview">>;
type InterviewWorkbenchKeepsNavActive = Expect<Equal<typeof interviewWorkbenchActiveKey, "interview">>;
