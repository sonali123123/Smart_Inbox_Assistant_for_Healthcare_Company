package com.smartinbox.repository;

import com.smartinbox.entity.ProcessingJob;
import com.smartinbox.model.JobStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ProcessingJobRepository extends JpaRepository<ProcessingJob, Long> {
    List<ProcessingJob> findByStatusOrderByCreatedAtAsc(JobStatus status);
    List<ProcessingJob> findByBatchId(String batchId);
    Optional<ProcessingJob> findFirstByMessageIdOrderByCreatedAtDesc(Long messageId);
}
