import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("publisher", Path(__file__).with_name("publish-go-whassup.py"))
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)

BASE = '''class GoWhassup < Formula
  url "https://github.com/wasichu/go-whassup/archive/refs/tags/v0.4.1.tar.gz"
  sha256 "'''+"a"*64+'''"

  bottle do
    root_url "https://example.com/old-bottles"
    sha256 arm64_tahoe: "old"
  end

  depends_on "go" => :build
end
'''
DIGEST = "b" * 64


class ReleasePolicyTests(unittest.TestCase):
    def test_only_url_checksum_and_old_bottles_change(self):
        updated = publisher.expected_formula(BASE, "v0.4.2", DIGEST)
        self.assertIn("v0.4.2.tar.gz", updated)
        self.assertIn(DIGEST, updated)
        self.assertNotIn("bottle do", updated)
        self.assertIn('depends_on "go" => :build', updated)
        publisher.validate_formula(BASE, updated, "v0.4.2", DIGEST)
        with self.assertRaises(ValueError):
            publisher.validate_formula(BASE, updated.replace('depends_on "go"', 'depends_on "unexpected"'), "v0.4.2", DIGEST)

    def test_prereleases_and_shell_text_are_rejected(self):
        for tag in ["v0.4.2-rc.1", "main", "v0.4.2; echo secret", "v0.4.2\n"]:
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                publisher.version(tag)

    def test_cannot_downgrade_or_republish_same_version(self):
        for tag in ["v0.3.0", "v0.4.1"]:
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                publisher.expected_formula(BASE, tag, DIGEST)

    def test_unknown_source_and_bad_hash_are_rejected(self):
        with self.assertRaises(ValueError):
            publisher.expected_formula(BASE.replace("wasichu/go-whassup", "other/repo"), "v0.4.2", DIGEST)
        with self.assertRaises(ValueError):
            publisher.expected_formula(BASE, "v0.4.2", "not-a-hash")

    def test_same_repo_bot_pr_and_exact_head_are_required(self):
        pr = {"state": "open", "draft": False, "head": {"sha": "a"*40, "repo": {"full_name": "wasichu/homebrew-tap"}},
              "base": {"ref": "main"}, "user": {"login": "github-actions[bot]"}}
        files = [{"filename": publisher.FORMULA, "status": "modified"}]
        with patch.object(publisher, "api", side_effect=[pr, files]):
            publisher.check_pr("wasichu/homebrew-tap", 5, "a"*40)
        for field, value in [("state", "closed"), ("draft", True)]:
            with self.subTest(field=field), patch.object(publisher, "api", return_value={**pr, field: value}), self.assertRaises(ValueError):
                publisher.check_pr("wasichu/homebrew-tap", 5, "a"*40)
        with patch.object(publisher, "api", return_value=pr), self.assertRaises(ValueError):
            publisher.check_pr("wasichu/homebrew-tap", 5, "b"*40)
        with patch.object(publisher, "api", side_effect=[pr, files + [{"filename": ".github/workflows/tests.yml", "status": "modified"}]]), self.assertRaises(ValueError):
            publisher.check_pr("wasichu/homebrew-tap", 5, "a"*40)

    def test_failed_build_is_not_published_or_dispatched_repeatedly(self):
        failed = {"id": 123, "status": "completed", "head_sha": "a"*40,
                  "conclusion": "failure", "html_url": "https://example.com/failed"}
        with patch.object(publisher, "api", side_effect=[{"workflow_runs": [failed]}, failed]) as api, self.assertRaises(RuntimeError):
            publisher.wait_run("wasichu/homebrew-tap", "tests.yml", "branch", {}, lambda run: True)
        self.assertEqual(api.call_count, 2)
        self.assertTrue(all(len(call.args) == 1 for call in api.call_args_list))

    def test_current_release_does_not_dispatch_or_mutate(self):
        release = {"tag_name": "v0.4.1", "draft": False, "prerelease": False}
        with patch.dict("os.environ", {"GITHUB_REPOSITORY": "wasichu/homebrew-tap"}), patch.object(publisher, "api", return_value=release) as api, patch.object(publisher, "formula", return_value=BASE), patch.object(publisher, "wait_run") as wait:
            publisher.main()
            api.assert_called_once()
            wait.assert_not_called()


if __name__ == "__main__":
    unittest.main()
