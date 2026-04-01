import { useCheckpoints } from "../hooks/useCheckpoints";

export function CheckpointsList() {
    const { data, loading, error } = useCheckpoints();
    const items: any[] = Array.isArray(data) ? data : [];

    if (loading) return <div>Loading checkpoints...</div>;
    if (error) return <div>Error loading checkpoints: {String(error)}</div>;
    if (items.length === 0) return <div>No checkpoints found.</div>;

    return (
        <div>
            <h2>Checkpoints</h2>
            <ul>
                {items.map((item: any, idx: number) => (
                    <li key={item.id || idx}>{JSON.stringify(item)}</li>
                ))}
            </ul>
        </div>
    );
}
