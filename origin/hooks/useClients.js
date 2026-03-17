import { useStudents } from "./useStudents";

export function useClients() {
  const { data, loading, error, refresh } = useStudents();
  return { data, loading, error, refresh };
}

