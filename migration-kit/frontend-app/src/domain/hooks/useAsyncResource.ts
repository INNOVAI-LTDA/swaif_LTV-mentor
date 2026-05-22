import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toUserErrorMessage } from "../../shared/api/types";

export type ResourceStatus = "idle" | "loading" | "success" | "empty" | "error";

type Options<T> = {
  enabled?: boolean;
  initialData: T;
  isEmpty?: (data: T) => boolean;
  resourceName?: string;
};

export function useAsyncResource<T>(
  loader: () => Promise<T>,
  deps: ReadonlyArray<unknown>,
  options: Options<T>
) {
  const { enabled = true, initialData, isEmpty, resourceName = "recurso" } = options;
  const mountedRef = useRef(true);
  const [data, setData] = useState<T>(initialData);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<ResourceStatus>(enabled ? "loading" : "idle");

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const refresh = useCallback(async () => {
    if (!enabled) {
      if (mountedRef.current) {
        setData(initialData);
        setError(null);
        setStatus("idle");
      }
      return initialData;
    }

    if (mountedRef.current) {
      setStatus("loading");
      setError(null);
    }

    try {
      const result = await loader();
      if (!mountedRef.current) {
        return result;
      }
      setData(result);
      const empty = isEmpty ? isEmpty(result) : false;
      setStatus(empty ? "empty" : "success");
      return result;
    } catch (err) {
      if (!mountedRef.current) {
        return initialData;
      }
      setError(toUserErrorMessage(err, `Falha ao carregar ${resourceName}.`));
      setStatus("error");
      return initialData;
    }
  }, [enabled, initialData, isEmpty, loader, resourceName]);

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return useMemo(
    () => ({
      data,
      error,
      status,
      loading: status === "loading",
      refresh,
      setData
    }),
    [data, error, status, refresh]
  );
}
