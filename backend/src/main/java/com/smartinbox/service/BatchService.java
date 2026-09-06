package com.smartinbox.service;

import com.smartinbox.dto.BatchStatusResponse;
import com.smartinbox.entity.Message;
import com.smartinbox.entity.ProcessingJob;
import com.smartinbox.model.JobStatus;
import com.smartinbox.repository.MessageRepository;
import com.smartinbox.repository.ProcessingJobRepository;
import jakarta.mail.Session;
import jakarta.mail.internet.MimeMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.FileInputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Properties;
import java.util.UUID;
import java.util.stream.Stream;

@Service
@RequiredArgsConstructor
@Slf4j
public class BatchService {

    private final MailIngestionService mailIngestionService;
    private final MessageRepository messageRepository;
    private final ProcessingJobRepository processingJobRepository;
    private final JobWorkerService jobWorkerService;

    public String runBatch(String sourceDir) {
        String batchId = "batch-" + UUID.randomUUID().toString().substring(0, 8);
        log.info("Starting batch run ID: {} from directory: {}", batchId, sourceDir);

        Path dirPath = Paths.get(sourceDir);
        if (!Files.exists(dirPath)) {
            // Check relative to parent directory (common when backend runs from backend/ directory)
            dirPath = Paths.get("..").resolve(sourceDir);
        }
        if (!Files.exists(dirPath)) {
            dirPath = Paths.get(".").resolve(sourceDir);
        }
        if (!Files.exists(dirPath)) {
            String userDir = System.getProperty("user.dir", ".");
            Path candidate = Paths.get(userDir).resolve(sourceDir);
            if (Files.exists(candidate)) {
                dirPath = candidate;
            } else if (Paths.get(userDir).getParent() != null && Files.exists(Paths.get(userDir).getParent().resolve(sourceDir))) {
                dirPath = Paths.get(userDir).getParent().resolve(sourceDir);
            }
        }

        dirPath = dirPath.toAbsolutePath().normalize();
        if (!Files.exists(dirPath)) {
            throw new IllegalArgumentException("Source directory not found: " + sourceDir + " (resolved to: " + dirPath + ")");
        }

        List<File> emlFiles = new ArrayList<>();
        try (Stream<Path> stream = Files.walk(dirPath)) {
            stream.filter(p -> p.toString().toLowerCase().endsWith(".eml"))
                  .forEach(p -> emlFiles.add(p.toFile()));
        } catch (Exception e) {
            throw new RuntimeException("Failed to scan directory for .eml files: " + e.getMessage(), e);
        }

        log.info("Found {} .eml files in directory {}", emlFiles.size(), sourceDir);

        Session session = Session.getDefaultInstance(new Properties());
        for (File file : emlFiles) {
            try (FileInputStream fis = new FileInputStream(file)) {
                MimeMessage mimeMessage = new MimeMessage(session, fis);

                String[] msgIds = mimeMessage.getHeader("Message-ID");
                String messageIdHeader = (msgIds != null && msgIds.length > 0) ? msgIds[0] : "batch-" + file.getName() + "-" + UUID.randomUUID();

                Message savedMessage;
                Optional<Message> existing = messageRepository.findByMessageIdHeader(messageIdHeader);
                if (existing.isPresent()) {
                    savedMessage = existing.get();
                    log.info("Message already exists for Message-ID: {}, re-queuing for batch {}", messageIdHeader, batchId);
                } else {
                    savedMessage = mailIngestionService.saveMessageAndAttachments(mimeMessage, messageIdHeader);
                }

                ProcessingJob job = ProcessingJob.builder()
                        .message(savedMessage)
                        .batchId(batchId)
                        .status(JobStatus.QUEUED)
                        .build();
                job = processingJobRepository.save(job);

                // Queue worker
                jobWorkerService.processJobAsync(job.getId());
                log.info("Queued batch job ID: {} for file: {}", job.getId(), file.getName());
            } catch (Exception e) {
                log.error("Failed to process batch file {}: {}", file.getName(), e.getMessage(), e);
            }
        }

        return batchId;
    }

    public BatchStatusResponse getBatchStatus(String batchId) {
        List<ProcessingJob> jobs = processingJobRepository.findByBatchId(batchId);

        List<BatchStatusResponse.DocumentStatus> docs = new ArrayList<>();
        for (ProcessingJob job : jobs) {
            String filename = job.getMessage() != null && job.getMessage().getSubject() != null
                    ? job.getMessage().getSubject()
                    : "Job-" + job.getId();

            Long msgId = job.getMessage() != null ? job.getMessage().getId() : null;
            docs.add(BatchStatusResponse.DocumentStatus.builder()
                    .filename(filename)
                    .status(job.getStatus().name())
                    .durationMs(job.getDurationMs())
                    .errorMessage(job.getErrorMessage())
                    .messageId(msgId)
                    .build());
        }

        return BatchStatusResponse.builder()
                .batchId(batchId)
                .documents(docs)
                .build();
    }
}
