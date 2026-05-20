import {
  alignLocalLoopbackApiBaseUrl,
} from "./env";

type Equal<Actual, Expected> =
  (<Value>() => Value extends Actual ? 1 : 2) extends
  (<Value>() => Value extends Expected ? 1 : 2)
    ? true
    : false;

type Expect<Condition extends true> = Condition;

const explicitLoopbackFromLocalhost = alignLocalLoopbackApiBaseUrl(
  "http://127.0.0.1:8001/api/v1",
  { hostname: "localhost", port: "5173" },
);
const explicitLocalhostFromLoopback = alignLocalLoopbackApiBaseUrl(
  "http://localhost:8001/api/v1",
  { hostname: "127.0.0.1", port: "5173" },
);
const productionApiBase = alignLocalLoopbackApiBaseUrl(
  "http://127.0.0.1:8001/api/v1",
  { hostname: "localhost", port: "443" },
);
const remoteApiBase = alignLocalLoopbackApiBaseUrl(
  "https://api.example.com/api/v1",
  { hostname: "localhost", port: "5173" },
);

type ExplicitLoopbackFromLocalhostUsesSameOriginProxy = Expect<
  Equal<typeof explicitLoopbackFromLocalhost, "/api/v1">
>;
type ExplicitLocalhostFromLoopbackUsesSameOriginProxy = Expect<
  Equal<typeof explicitLocalhostFromLoopback, "/api/v1">
>;
type NonDevPortKeepsConfiguredApiHost = Expect<
  Equal<typeof productionApiBase, "http://127.0.0.1:8001/api/v1">
>;
type RemoteApiBaseKeepsConfiguredHost = Expect<
  Equal<typeof remoteApiBase, "https://api.example.com/api/v1">
>;

void explicitLoopbackFromLocalhost;
void explicitLocalhostFromLoopback;
void productionApiBase;
void remoteApiBase;
