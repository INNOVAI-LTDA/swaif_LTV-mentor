import { useEnrollments } from "../hooks/useEnrollments";

export function EnrollmentsList() {
    const { data, loading, error } = useEnrollments();
    const items: any[] = Array.isArray(data) ? data : [];

    if (loading) return <div>Loading enrollments...</div>;
    if (error) return <div>Error loading enrollments: {String(error)}</div>;
    if (items.length === 0) return <div>No enrollments found.</div>;

    return (
        <div>
            <h2>Enrollments</h2>
            <ul>
                {items.map((item: any, idx: number) => (
                    <li key={item.id || idx}>{JSON.stringify(item)}</li>
                ))}
            </ul>
        </div>
    );
}
