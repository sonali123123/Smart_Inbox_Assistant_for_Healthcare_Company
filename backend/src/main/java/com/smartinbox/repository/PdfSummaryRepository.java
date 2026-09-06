package com.smartinbox.repository;

import com.smartinbox.entity.PdfSummary;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface PdfSummaryRepository extends JpaRepository<PdfSummary, Long> {
    Optional<PdfSummary> findByAttachmentId(Long attachmentId);
}
