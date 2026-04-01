import { useProtocols } from "../hooks/useProtocols";

export function ProtocolsList() {
    const { data, loading, error } = useProtocols();
    const items: any[] = Array.isArray(data) ? data : [];

    if (loading) return <div>Loading protocols...</div>;
    if (error) return <div>Error loading protocols: {String(error)}</div>;
    if (items.length === 0) return <div>No protocols found.</div>;

    return (
        <div>
            <h2>Protocols</h2>
            <ul>
                {items.map((item: any, idx: number) => (
                    <li key={item.id || idx}>{JSON.stringify(item)}</li>
                ))}
            </ul>
        </div>
    );
}
