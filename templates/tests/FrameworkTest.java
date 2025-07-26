import org.junit.Test;
import org.junit.Assert;

/**
 * AI-First SDLC Framework Test
 * This is a placeholder test that verifies the framework is set up correctly.
 */
public class FrameworkTest {
    
    @Test
    public void testFrameworkSetup() {
        // This test always passes to indicate framework is installed
        Assert.assertTrue("AI-First SDLC Framework is set up", true);
    }
    
    @Test
    public void testProjectStructure() {
        // Verify essential directories exist
        Assert.assertTrue("docs directory should exist", 
            new java.io.File("docs").exists());
        Assert.assertTrue("retrospectives directory should exist", 
            new java.io.File("retrospectives").exists());
    }
}