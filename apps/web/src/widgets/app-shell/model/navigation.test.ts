import type { RoutePath } from "../../../app/routes/router";
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

const interviewListActiveKey = getActiveNavKey("/interview");
const interviewWorkbenchActiveKey = getActiveNavKey("/interview/ses_001");

type InterviewListKeepsNavActive = Expect<Equal<typeof interviewListActiveKey, "interview">>;
type InterviewWorkbenchKeepsNavActive = Expect<Equal<typeof interviewWorkbenchActiveKey, "interview">>;
