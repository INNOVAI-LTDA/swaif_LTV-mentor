import { useEffect, useState } from "react";

// TODO: Replace with actual session/context logic to get current student id
function getCurrentStudentId(): string | null {
    // Example: return "student_1";
    // In production, get from auth/session context
    return window.localStorage.getItem("student_id") || null;
}

export type StudentProfile = {
    id: string;
    name: string;
    email: string;
    avatar_url?: string;
    preferences: Record<string, unknown>;
    metadata: Record<string, unknown>;
};

export function useStudentProfile() {
    const [profile, setProfile] = useState<StudentProfile | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const studentId = getCurrentStudentId();

    useEffect(() => {
        if (!studentId) {
            setProfile(null);
            setLoading(false);
            setError("Aluno não encontrado.");
            return;
        }
        setLoading(true);
        fetch(`/api/student-profile?student_id=${studentId}`)
            .then((res) => {
                if (!res.ok) throw new Error("Erro ao buscar perfil do aluno");
                return res.json();
            })
            .then((data) => {
                setProfile(data.profile || null);
                setError(null);
            })
            .catch((err) => {
                setError(err.message || "Erro desconhecido");
                setProfile(null);
            })
            .finally(() => setLoading(false));
    }, [studentId]);

    return { profile, loading, error };
}
