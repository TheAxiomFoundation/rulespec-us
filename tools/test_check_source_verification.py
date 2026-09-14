import unittest
from check_source_verification import issues

class SourceVerificationTests(unittest.TestCase):
    def test_supplemental_values_and_multiple_source_records_are_preserved(self):
        self.assertEqual(issues({"module": {"source_verification": {"corpus_citation_path": "us/guidance/irs/rev-proc-2025-32"}, "source_values": {"limit": 42}, "source_documents": [{"corpus_citation_path": "page-14"}, {"corpus_citation_path": "page-15"}]}}), [])
    def test_snap_values_are_rejected_in_verification(self):
        self.assertTrue(any("unsupported field" in issue for issue in issues({"module": {"source_verification": {"corpus_citation_path": "source", "values": {"limit": 42}}}})))
    def test_plural_citations_are_rejected_even_in_nested_proofs(self):
        self.assertTrue(issues({"rules": [{"metadata": {"proof": {"source": {"corpus_citation_paths": ["a", "b"]}}}}]}))
    def test_missing_or_malformed_singular_citation_is_rejected(self):
        for value in [None, {}, {"corpus_citation_path": []}, {"corpus_citation_path": " "}]:
            self.assertTrue(issues({"module": {"source_verification": value}}))

if __name__ == "__main__":
    unittest.main()
