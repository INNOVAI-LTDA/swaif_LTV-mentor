import { useMeasurements } from "../hooks/useMeasurements";

export function MeasurementsList() {
    const { data, loading, error } = useMeasurements();
    const items: any[] = Array.isArray(data) ? data : [];

    if (loading) return <div>Loading measurements...</div>;
    if (error) return <div>Error loading measurements: {String(error)}</div>;
    if (items.length === 0) return <div>No measurements found.</div>;

    return (
        <div>
            <h2>Measurements</h2>
            <ul>
                {items.map((item: any, idx: number) => (
                    <li key={item.id || idx}>{JSON.stringify(item)}</li>
                ))}
            </ul>
        </div>
    );
}
