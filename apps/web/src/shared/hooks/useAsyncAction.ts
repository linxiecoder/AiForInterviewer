import { useCallback, useState } from "react";

export interface UseAsyncActionState {
  loading: boolean;
  error: string | null;
}

export interface UseAsyncActionResult<TArgs extends unknown[], TResult> extends UseAsyncActionState {
  execute: (...args: TArgs) => Promise<TResult>;
  clearError: () => void;
}

export function useAsyncAction<TArgs extends unknown[], TResult>(
  action: (...args: TArgs) => Promise<TResult>,
): UseAsyncActionResult<TArgs, TResult> {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(
    async (...args: TArgs): Promise<TResult> => {
      setLoading(true);
      setError(null);
      try {
        const result = await action(...args);
        return result;
      } catch (err) {
        setError(err instanceof Error ? err.message : "操作失败");
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [action],
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return { loading, error, execute, clearError };
}
