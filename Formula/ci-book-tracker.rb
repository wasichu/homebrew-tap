class CiBookTracker < Formula
  desc "Local-first reading tracker for language learners"
  homepage "https://github.com/wasichu/ci-book-tracker"
  url "https://github.com/wasichu/ci-book-tracker/releases/download/v0.1.0/ci-book-tracker-0.1.0-linux-x86_64.tar.gz"
  sha256 "91c8937726e434d794b8503e9db2692f4d3ab6d63754175826e5649e8b315a37"
  license "MIT"

  on_macos do
    depends_on macos: :sequoia
    depends_on "ncurses"
    depends_on "openssl@3"

    on_arm do
      url "https://github.com/wasichu/ci-book-tracker/releases/download/v0.1.0/ci-book-tracker-0.1.0-macos-arm64.tar.gz"
      sha256 "ec4548c8f554dfa965053dfa29fe435a5c554619288fa9ecebbb17bfc815169a"
    end
    on_intel do
      url "https://github.com/wasichu/ci-book-tracker/releases/download/v0.1.0/ci-book-tracker-0.1.0-macos-x86_64.tar.gz"
      sha256 "62533a6e4cd3756b01350d36c631535ccfd472eb8fe06cb7df2b99330efe6736"
    end
  end

  on_linux do
    depends_on arch: :x86_64
  end

  def install
    libexec.install Dir["*"]
    bin.write_exec_script libexec/"bin/ci-book-tracker"
  end

  def caveats
    <<~EOS
      Run ci-book-tracker, then open http://localhost:4000.
      Data and the automatically generated session secret live in your user data directory.
      Linux packages require Ubuntu 24.04 or compatible glibc 2.39+, OpenSSL 3 and ncurses 6.
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/ci-book-tracker --version")
    port = free_port
    pid = spawn({ "PORT" => port.to_s, "CI_BOOK_TRACKER_DATA_DIR" => testpath.to_s,
                  "DATABASE_PATH" => (testpath/"reading_log.db").to_s,
                  "SECRET_KEY_BASE" => "a" * 64 },
                bin/"ci-book-tracker", out: testpath/"server.log", err: [:child, :out])
    begin
      sleep 1
      response = shell_output("curl --fail --silent --retry 30 --retry-connrefused " \
                              "--retry-delay 1 http://127.0.0.1:#{port}")
      assert_match 'id="reading-log-selector"', response
    ensure
      Process.kill("TERM", pid)
      Process.wait(pid)
    end
  end
end
