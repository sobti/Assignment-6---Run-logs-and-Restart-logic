package Infrastructure;

public class CloudWebDriverFactory implements WebDriverFactory {
       public String create() {
        String testBrowser = ConfigurationManager.getInstance().getTestbrowser();
        switch (testBrowser) {
            case "chrome":
                return "cloud new chrome driver";
            case "firefox":
                return "cloud new firefox driver";
            default:
                return "";
        }


    }
}
