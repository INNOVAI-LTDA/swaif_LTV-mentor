from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.measurement_overall_repository import MeasurementOverallRepository

def main():
    enrollments = EnrollmentRepository().list_enrollments()
    repo = MeasurementOverallRepository()

    if not enrollments:
        repo._write_items([])
        return

    repo.generate_for_all_enrollments()

if __name__ == "__main__":
    main()
