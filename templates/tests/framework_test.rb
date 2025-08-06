require 'minitest/autorun'

# AI-First SDLC Framework Test
# This is a placeholder test that verifies the framework is set up correctly.
class FrameworkTest < Minitest::Test
  def test_framework_setup
    # This test always passes to indicate framework is installed
    assert true, "AI-First SDLC Framework is set up"
  end

  def test_project_structure
    # Verify essential directories exist
    assert File.directory?('docs'), "docs directory should exist"
    assert File.directory?('retrospectives'), "retrospectives directory should exist"
    assert File.exist?('CLAUDE.md'), "CLAUDE.md should exist"
  end

  def test_version_file
    # Check VERSION file exists
    assert File.exist?('VERSION'), "VERSION file should exist"
  end
end