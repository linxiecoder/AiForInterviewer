import { AppProviders } from "./providers/AppProviders";
import { AppRouter, RouteProvider } from "./routes/router";

export function App() {
  return (
    <AppProviders>
      <RouteProvider>
        <AppRouter />
      </RouteProvider>
    </AppProviders>
  );
}
