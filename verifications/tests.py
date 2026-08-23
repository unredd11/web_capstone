from django.test import SimpleTestCase

from verifications.models import AuditLog, BlockchainRecord, InspectionImage, VerificationReport


class VerificationSchemaTests(SimpleTestCase):
    def test_report_contains_review_and_progress_fields(self):
        field_names = {field.name for field in VerificationReport._meta.get_fields()}

        self.assertTrue({
            'progress_percentage',
            'accomplishment_description',
            'reviewed_by',
            'reviewed_at',
            'review_notes',
        }.issubset(field_names))

    def test_inspection_image_contains_authentication_metadata(self):
        field_names = {field.name for field in InspectionImage._meta.get_fields()}

        self.assertTrue({
            'image_file',
            'sha256_hash',
            'perceptual_hash',
            'latitude',
            'longitude',
            'gps_accuracy',
            'captured_at',
            'geofence_distance',
            'geofence_status',
        }.issubset(field_names))

    def test_blockchain_receipt_is_one_to_one_with_image(self):
        field = BlockchainRecord._meta.get_field('inspection_image')

        self.assertTrue(field.one_to_one)

    def test_audit_log_keeps_user_optional(self):
        field = AuditLog._meta.get_field('user')

        self.assertTrue(field.null)
        self.assertEqual(field.remote_field.on_delete.__name__, 'SET_NULL')
