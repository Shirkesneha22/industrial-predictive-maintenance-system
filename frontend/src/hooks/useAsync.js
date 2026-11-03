import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook to execute asynchronous functions with loading, error, and data state.
 * @param {Function} asyncFn - Async function returning a promise
 * @param {Array} [deps=[]] - Dependency array to trigger refetch
 * @param {boolean} [immediate=true] - Whether to execute immediately
 */
export function useAsync(asyncFn, deps = [], immediate = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);

  // Keep track of mounted status to prevent memory leak updates
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  const execute = useCallback(
    async (...args) => {
      setLoading(true);
      setError(null);
      try {
        const result = await asyncFn(...args);
        if (isMounted.current) {
          setData(result);
          setLoading(false);
        }
        return result;
      } catch (err) {
        if (isMounted.current) {
          setError(err);
          setLoading(false);
        }
        throw err;
      }
    },
    [asyncFn]
  );

  useEffect(() => {
    if (immediate) {
      execute().catch(() => {
        // Error already handled in state
      });
    }
  }, deps);

  return {
    data,
    loading,
    error,
    execute,
    refetch: execute,
    setData,
  };
}

export default useAsync;
