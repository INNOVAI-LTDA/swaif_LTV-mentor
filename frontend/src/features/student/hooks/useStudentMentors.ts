import { useEffect, useState } from "react";

// TODO: Replace with actual session/context logic to get current student id
function getCurrentStudentId(): string | null {
    // Example: return "student_1";
    // In production, get from auth/session context
    return window.localStorage.getItem("student_id") || null;
}

export type StudentMentor = {
    id: string;
    name: string;
    email: string;
    role: string;
    avatar_url?: string;
    main: boolean;
    metadata: Record<string, unknown>;
};

export function useStudentMentors() {
    const [mentors, setMentors] = useState<StudentMentor[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const studentId = getCurrentStudentId();

    useEffect(() => {
        if (!studentId) {
            setMentors([]);
            setLoading(false);
            setError("Aluno não encontrado.");
            return;
        }
        setLoading(true);
        fetch(`/api/student-mentors?student_id=${studentId}`)
            .then((res) => {
                if (!res.ok) throw new Error("Erro ao buscar mentores do aluno");
                return res.json();
            })
            .then((data) => {
                setMentors(Array.isArray(data.items) ? data.items : []);
                setError(null);
            })
            .catch((err) => {
                setError(err.message || "Erro desconhecido");
                setMentors([]);
            })
            .finally(() => setLoading(false));
    }, [studentId]);

    return { mentors, loading, error };
}
