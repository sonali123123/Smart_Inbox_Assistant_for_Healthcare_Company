package com.smartinbox.service;

import com.smartinbox.entity.ProcessingJob;
import com.smartinbox.model.JobStatus;
import com.smartinbox.repository.ProcessingJobRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class JobWorkerService {

    private final ProcessingJobRepository processingJobRepository;
    private final DocumentProcessingService documentProcessingService;

    @Async("jobTaskExecutor")
    public void processJobAsync(Long jobId) {
        processJob(jobId);
    }

    public void processJob(Long jobId) {
        ProcessingJob job = processingJobRepository.findById(jobId).orElse(null);
        if (job == null || job.getStatus() != JobStatus.QUEUED) {
            return;
        }

        job.setStatus(JobStatus.PROCESSING);
        job.setStartedAt(LocalDateTime.now());
        processingJobRepository.save(job);

        log.info("Processing job ID: {} for message ID: {}", job.getId(), job.getMessage().getId());

        try {
            documentProcessingService.processMessage(job.getMessage().getId());

            job.setStatus(JobStatus.DONE);
            job.setCompletedAt(LocalDateTime.now());
            job.setDurationMs(Duration.between(job.getStartedAt(), job.getCompletedAt()).toMillis());
            processingJobRepository.save(job);

            log.info("Job ID: {} completed successfully in {} ms", job.getId(), job.getDurationMs());
        } catch (Exception e) {
            log.error("Job ID: {} failed: {}", job.getId(), e.getMessage(), e);

            job.setStatus(JobStatus.FAILED);
            job.setCompletedAt(LocalDateTime.now());
            job.setDurationMs(Duration.between(job.getStartedAt(), job.getCompletedAt()).toMillis());
            job.setErrorMessage(e.getMessage() != null ? e.getMessage().substring(0, Math.min(1990, e.getMessage().length())) : "Unknown error");
            processingJobRepository.save(job);
        }
    }

    @Scheduled(fixedDelay = 5000)
    public void pollQueue() {
        List<ProcessingJob> queuedJobs = processingJobRepository.findByStatusOrderByCreatedAtAsc(JobStatus.QUEUED);
        if (!queuedJobs.isEmpty()) {
            log.debug("Found {} queued processing jobs", queuedJobs.size());
            for (ProcessingJob job : queuedJobs) {
                try {
                    processJob(job.getId());
                } catch (Exception e) {
                    log.error("Failed to trigger job {}: {}", job.getId(), e.getMessage());
                }
            }
        }
    }
}
