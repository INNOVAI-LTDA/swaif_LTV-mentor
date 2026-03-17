import { useCallback, useEffect, useRef, useState } from "react";
import { getHttpStatus, toUserErrorMessage } from "../lib/errors.js";
import { logResourceFailure } from "../lib/integrationLogger.js";

export function useAsyncResource(loader, deps = [], options = {}) {
  const { enabled = true, initialData = null, resourceName = "recurso" } = options;
  const mountedRef = useRef(true);
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(Boolean(enabled));
  const [error, setError] = useState(null);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const run = useCallback(async () => {
    if (!enabled) {
      setLoading(false);
      return initialData;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await loader();
      if (mountedRef.current) setData(result);
      return result;
    } catch (err) {
      const message = toUserErrorMessage(
        err,
        `Falha ao carregar ${resourceName}.`
      );
      if (mountedRef.current) setError(message);
      logResourceFailure({
        resource: resourceName,
        status: getHttpStatus(err),
        code: err?.code || "UNKNOWN_ERROR",
        message,
      });
      return null;
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [enabled, initialData, loader, resourceName]);

  useEffect(() => {
    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error, refresh: run, setData };
}
