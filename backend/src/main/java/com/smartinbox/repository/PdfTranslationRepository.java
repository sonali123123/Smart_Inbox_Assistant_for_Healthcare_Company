package com.smartinbox.repository;

import com.smartinbox.entity.PdfTranslation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface PdfTranslationRepository extends JpaRepository<PdfTranslation, Long> {
    Optional<PdfTranslation> findByAttachmentId(Long attachmentId);
}
