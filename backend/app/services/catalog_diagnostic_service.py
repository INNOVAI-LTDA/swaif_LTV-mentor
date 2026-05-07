from __future__ import annotations

from typing import Any

from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.measurement_repository import MeasurementRepository
from app.storage.metric_repository import MetricRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository
from app.storage.student_repository import StudentRepository


class CatalogDiagnosticService:
    def __init__(self, *, protocols: ProtocolRepository, pillars: PillarRepository, metrics: MetricRepository, enrollments: EnrollmentRepository, measurements: MeasurementRepository, students: StudentRepository) -> None:
        self._protocols = protocols
        self._pillars = pillars
        self._metrics = metrics
        self._enrollments = enrollments
        self._measurements = measurements
        self._students = students

    def build_report(self) -> dict[str, Any]:
        products = self._protocols.list_protocols()
        pillars = self._pillars.list_pillars()
        metrics = self._metrics.list_metrics()
        enrollments = self._enrollments.list_enrollments()
        measurements = self._measurements.list_measurements()
        students_by_id = {str(s.get('id')): s for s in self._students.list_students() if s.get('id')}

        pillars_by_product: dict[str, list[dict[str, Any]]] = {}
        for p in pillars:
            product_id = str(p.get('product_id') or p.get('protocol_id') or '')
            if product_id:
                pillars_by_product.setdefault(product_id, []).append(p)
        metrics_by_pillar: dict[str, list[dict[str, Any]]] = {}
        for m in metrics:
            metrics_by_pillar.setdefault(str(m.get('pillar_id') or ''), []).append(m)

        metric_ids_with_data = {str(m.get('metric_id') or '') for m in measurements if m.get('metric_id')}

        report_products = []
        coverage_errors: list[dict[str, Any]] = []
        for product in products:
            product_id = str(product.get('id') or '')
            expected = sorted(pillars_by_product.get(product_id, []), key=lambda x: int(x.get('order_index', 999)))
            present = [p for p in expected if p.get('id')]
            pillar_rows = []
            for p in expected:
                pid = str(p.get('id') or '')
                pmetrics = metrics_by_pillar.get(pid, [])
                has_metrics = len(pmetrics) > 0
                if not has_metrics:
                    coverage_errors.append({'product_id': product_id, 'pillar_id': pid, 'issue': 'pillar_without_metric'})
                pillar_rows.append({
                    'pillar_id': pid,
                    'pillar_name': str(p.get('name') or ''),
                    'metrics_count': len(pmetrics),
                    'metric_ids': [str(m.get('id')) for m in pmetrics if m.get('id')],
                })
            incomplete_students = []
            for e in [x for x in enrollments if str(x.get('organization_id') or '') == product_id and bool(x.get('is_active', True))]:
                sid = str(e.get('student_id') or '')
                expected_metric_ids = {mid for row in pillar_rows for mid in row['metric_ids']}
                measured_ids = {str(mea.get('metric_id')) for mea in measurements if str(mea.get('enrollment_id') or '') == str(e.get('id') or '')}
                missing = sorted(expected_metric_ids - measured_ids)
                if missing:
                    incomplete_students.append({'student_id': sid, 'student_name': str((students_by_id.get(sid) or {}).get('full_name') or sid), 'missing_metric_ids': missing})
            report_products.append({
                'product_id': product_id,
                'product_name': str(product.get('name') or ''),
                'expected_pillars': [str(p.get('id')) for p in expected],
                'present_pillars': [str(p.get('id')) for p in present],
                'pillars': pillar_rows,
                'students_with_incomplete_data': incomplete_students,
            })

        return {
            'canonical_source': 'backend/data_new/pillars.json (seed catalog por produto)',
            'coverage_ok': len(coverage_errors) == 0,
            'coverage_errors': coverage_errors,
            'products': report_products,
            'metrics_with_data_count': len(metric_ids_with_data),
        }
