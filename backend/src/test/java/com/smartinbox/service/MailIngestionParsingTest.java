package com.smartinbox.service;

import jakarta.mail.Session;
import jakarta.mail.internet.MimeMessage;
import org.junit.jupiter.api.Test;

import java.io.File;
import java.io.FileInputStream;
import java.util.Properties;

import static org.junit.jupiter.api.Assertions.*;

public class MailIngestionParsingTest {

    @Test
    void testParseSampleEmlFiles() throws Exception {
        File emlDir = new File("../test-data/emails");
        if (!emlDir.exists()) {
            emlDir = new File("test-data/emails");
        }
        assertTrue(emlDir.exists(), "test-data/emails directory should exist");

        File[] files = emlDir.listFiles((dir, name) -> name.endsWith(".eml"));
        assertNotNull(files);
        assertTrue(files.length >= 10, "Should have at least 10 sample emails for testing");

        Session session = Session.getDefaultInstance(new Properties());

        for (File file : files) {
            try (FileInputStream fis = new FileInputStream(file)) {
                MimeMessage msg = new MimeMessage(session, fis);

                assertNotNull(msg.getSubject(), "Email should have a subject: " + file.getName());
                assertNotNull(msg.getFrom(), "Email should have a sender: " + file.getName());
                assertTrue(msg.getFrom().length > 0, "Sender should not be empty: " + file.getName());

                // Check content is accessible
                assertNotNull(msg.getContent(), "Message content should not be null: " + file.getName());
            }
        }
    }
}
