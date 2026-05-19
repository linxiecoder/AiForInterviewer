import type { RoutePath } from "../../../app/routes/router";
import { APP_SHELL_NAV_ITEMS } from "./navigation";

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
type InterviewNavPathIsInterview = Expect<Equal<InterviewNavItem["path"], "/interview">>;
type InterviewNavIsEnabled = Expect<Equal<InterviewNavItem["disabled"], false>>;
