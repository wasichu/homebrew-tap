class GoWhassup < Formula
  desc "WhatsApp client for the terminal"
  homepage "https://github.com/wasichu/go-whassup"
  url "https://github.com/wasichu/go-whassup/archive/refs/tags/v0.4.0.tar.gz"
  sha256 "a0f2bc73e22b5318b41a21bcd4ee7c26fa1fe109cc88cad90286c295e8b7e980"
  license "MPL-2.0"
  head "https://github.com/wasichu/go-whassup.git", branch: "main"

  bottle do
    root_url "https://github.com/wasichu/homebrew-tap/releases/download/go-whassup-0.4.0"
    sha256 cellar: :any_skip_relocation, arm64_tahoe:  "c07ab755b2700d9a5b0d9447071041903e5e0576aae870a5288b430c8bb8a382"
    sha256 cellar: :any_skip_relocation, x86_64_linux: "1f88e1f05d5b10f5ba500b1f39dda39d1f99938350ab79aa5d202415d09ad45e"
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
