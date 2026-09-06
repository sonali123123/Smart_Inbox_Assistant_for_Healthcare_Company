package com.smartinbox.repository;

import com.smartinbox.entity.LiteratureCase;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface LiteratureCaseRepository extends JpaRepository<LiteratureCase, Long> {
    List<LiteratureCase> findByBatchIdOrderByCaseIndexAsc(String batchId);
    List<LiteratureCase> findBySourceAttachmentId(Long sourceAttachmentId);
    java.util.Optional<LiteratureCase> findByMessageId(Long messageId);
}
