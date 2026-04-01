import { useEffect, useState } from "react";

export function useUsers() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        setLoading(true);
        fetch("/api/admin/users")
            .then((res) => {
                if (!res.ok) throw new Error("Failed to fetch users");
                return res.json();
            })
            .then((data) => {
                setData(data);
                setError(null);
            })
            .catch((err) => {
                setError(err);
                setData(null);
            })
            .finally(() => setLoading(false));
    }, []);

    return { data, loading, error };
}
