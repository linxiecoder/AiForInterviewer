import { APP_DOCUMENT_VIEWPORT_POLICY } from "./AppShell";

type Equal<Actual, Expected> =
  (<Value>() => Value extends Actual ? 1 : 2) extends
  (<Value>() => Value extends Expected ? 1 : 2)
    ? true
    : false;

type Expect<Condition extends true> = Condition;

type DocumentViewportPreventsGlobalScrollbar = Expect<
  Equal<
    typeof APP_DOCUMENT_VIEWPORT_POLICY,
    {
      readonly htmlOverflow: "hidden";
      readonly bodyOverflow: "hidden";
      readonly rootOverflow: "hidden";
      readonly shellOverflow: "hidden";
      readonly mainContentOverflow: "auto";
    }
  >
>;

void APP_DOCUMENT_VIEWPORT_POLICY;
