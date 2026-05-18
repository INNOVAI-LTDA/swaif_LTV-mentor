import { useUsers } from "../hooks/useUsers";

export function UsersList() {
    const { data, loading, error } = useUsers();
    const items: any[] = Array.isArray(data) ? data : [];

    if (loading) return <div>Loading users...</div>;
    if (error) return <div>Error loading users: {String(error)}</div>;
    if (items.length === 0) return <div>No users found.</div>;

    return (
        <div>
            <h2>Users</h2>
            <ul>
                {items.map((item: any, idx: number) => (
                    <li key={item.id || idx}>{JSON.stringify(item)}</li>
                ))}
            </ul>
        </div>
    );
}
