import { useEffect, useState } from "react";

// TODO: Replace with actual session/context logic to get current student/org
function getCurrentStudentId(): string | null {
    // Example: return "student_1";
    // In production, get from auth/session context
    return window.localStorage.getItem("student_id") || null;
}

export type StudentProduct = {
    id: string;
    name: string;
    code: string;
    status: string;
    mentor_id: string;
    start_date: string;
    end_date: string | null;
    metadata: Record<string, unknown>;
};

export function useStudentProducts() {
    const [products, setProducts] = useState<StudentProduct[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const studentId = getCurrentStudentId();

    useEffect(() => {
        if (!studentId) {
            setProducts([]);
            setLoading(false);
            setError("Aluno não encontrado.");
            return;
        }
        setLoading(true);
        fetch(`/api/student-products?student_id=${studentId}`)
            .then((res) => {
                if (!res.ok) throw new Error("Erro ao buscar produtos do aluno");
                return res.json();
            })
            .then((data) => {
                setProducts(Array.isArray(data.items) ? data.items : []);
                setError(null);
            })
            .catch((err) => {
                setError(err.message || "Erro desconhecido");
                setProducts([]);
            })
            .finally(() => setLoading(false));
    }, [studentId]);

    return { products, loading, error };
}
