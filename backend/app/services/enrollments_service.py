from backend.app.storage.enrollment_repository import EnrollmentRepository
from backend.app.schemas.enrollment import EnrollmentCreate, Enrollment
from typing import List

def get_all_enrollments() -> List[Enrollment]:
    repo = EnrollmentRepository()
    return repo.list_enrollments()

def create_enrollment(enrollment_data: EnrollmentCreate) -> Enrollment:
    repo = EnrollmentRepository()
    return repo.create_enrollment(enrollment_data)
