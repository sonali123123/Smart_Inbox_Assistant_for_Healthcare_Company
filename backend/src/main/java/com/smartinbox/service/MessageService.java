package com.smartinbox.service;

import com.smartinbox.config.AppProperties;
import jakarta.persistence.EntityManager;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.io.FileUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

@Service
@RequiredArgsConstructor
@Slf4j
public class MessageService {

    private final EntityManager entityManager;
    private final AppProperties appProperties;

    @Transactional
    public void resetAllData() {
        log.warn("Executing complete reset of all messages, extracted facts, and audit logs...");

        // Delete in reverse foreign-key dependency order
        entityManager.createNativeQuery("DELETE FROM AUDIT_LOG").executeUpdate();
        entityManager.createNativeQuery("DELETE FROM LITERATURE_CASES").executeUpdate();
        entityManager.createNativeQuery("DELETE FROM PROCESSING_JOBS").executeUpdate();
        entityManager.createNativeQuery("DELETE FROM REVIEW_ACTIONS").executeUpdate();
        entityManager.createNativeQuery("DELETE FROM EXTRACTED_FIELDS").executeUpdate();
        entityManager.createNativeQuery("DELETE FROM CLASSIFICATIONS").executeUpdate();
        entityManager.createNativeQuery("DELETE FROM PDF_SUMMARIES").executeUpdate();
        entityManager.createNativeQuery("DELETE FROM PDF_TABLES").executeUpdate();
        entityManager.createNativeQuery("DELETE FROM PDF_IMAGES").executeUpdate();
        entityManager.createNativeQuery("DELETE FROM PDF_TRANSLATIONS").executeUpdate();
        entityManager.createNativeQuery("DELETE FROM ATTACHMENTS").executeUpdate();
        entityManager.createNativeQuery("DELETE FROM MESSAGES").executeUpdate();

        cleanStorageDirectory();

        log.info("Reset complete. All tables and runtime storage cleaned.");
    }

    private void cleanStorageDirectory() {
        try {
            Path storagePath = Paths.get(appProperties.getStorage().getPath());
            if (!Files.exists(storagePath) && Files.exists(Paths.get("..").resolve(storagePath))) {
                storagePath = Paths.get("..").resolve(storagePath);
            }
            if (Files.exists(storagePath)) {
                File dir = storagePath.toFile();
                File[] files = dir.listFiles();
                if (files != null) {
                    for (File f : files) {
                        if (!f.getName().equals(".gitkeep")) {
                            if (f.isDirectory()) {
                                FileUtils.deleteDirectory(f);
                            } else {
                                f.delete();
                            }
                        }
                    }
                }
            }
        } catch (Exception e) {
            log.warn("Could not fully clean storage directory: {}", e.getMessage());
        }
    }
}
