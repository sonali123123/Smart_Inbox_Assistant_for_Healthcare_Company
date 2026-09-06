package com.smartinbox.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "app")
@Getter
@Setter
public class AppProperties {

    private AiService aiService = new AiService();
    private Storage storage = new Storage();
    private Mail mail = new Mail();

    @Getter
    @Setter
    public static class AiService {
        private String url = "http://localhost:8000";
        private int connectTimeoutMs = 10000;
        private int readTimeoutMs = 90000;
    }

    @Getter
    @Setter
    public static class Storage {
        private String path = "./storage";
    }

    @Getter
    @Setter
    public static class Mail {
        private String host = "imap.gmail.com";
        private int port = 993;
        private String protocol = "imaps";
        private String username;
        private String password;
        private String folder = "INBOX";
        private boolean pollEnabled = false;
        private String pollCron = "0 */5 * * * *";
    }
}
