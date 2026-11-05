class GoWhassup < Formula
  desc "WhatsApp client for the terminal"
  homepage "https://github.com/wasichu/go-whassup"
  url "https://github.com/wasichu/go-whassup/archive/refs/tags/v0.4.1.tar.gz"
  sha256 "c92784c7a775eeb2738bef1a11aedbd7f0c439ffca1263771b9476f3b10c34bf"
  license "MPL-2.0"
  head "https://github.com/wasichu/go-whassup.git", branch: "main"

  bottle do
    root_url "https://github.com/wasichu/homebrew-tap/releases/download/go-whassup-0.4.1"
    sha256 cellar: :any_skip_relocation, arm64_tahoe:  "eb3bd90668771f736571a6f1b5979a84c892f00b385ac5082d41bec8602617a8"
    sha256 cellar: :any_skip_relocation, x86_64_linux: "f8a990d7bb1972f45dfd5c7fb93b212498a887d322b4db7e7e0224b88b5f3fce"
  end

  depends_on "go" => :build

  def install
    ENV["CGO_ENABLED"] = "0" # pure-Go SQLite: a static binary, as in the releases
    ldflags = "-X github.com/wasichu/go-whassup/internal/app.Version=v#{version}"
    system "go", "build", *std_go_args(ldflags:), "./cmd/go-whassup"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/go-whassup -version")
  end
end
