class GoWhassup < Formula
  desc "WhatsApp client for the terminal"
  homepage "https://github.com/wasichu/go-whassup"
  url "https://github.com/wasichu/go-whassup/archive/refs/tags/v0.2.3.tar.gz"
  sha256 "d9b6bda2fa8fb1a7d3113d3bce95c66c78547c7f104e2e1d667d66615e7aa18a"
  license "MPL-2.0"
  head "https://github.com/wasichu/go-whassup.git", branch: "main"

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
