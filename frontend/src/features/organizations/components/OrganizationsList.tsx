import { useOrganizations } from "../hooks/useOrganizations";

export function OrganizationsList() {
    const { data, loading, error } = useOrganizations();
    const items: any[] = Array.isArray(data) ? data : [];

    if (loading) return <div>Loading organizations...</div>;
    if (error) return <div>Error loading organizations: {String(error)}</div>;
    if (items.length === 0) return <div>No organizations found.</div>;

    return (
        <div>
            <h2>Organizations</h2>
            <ul>
                {items.map((item: any, idx: number) => (
                    <li key={item.id || idx}>{JSON.stringify(item)}</li>
                ))}
            </ul>
        </div>
    );
}
