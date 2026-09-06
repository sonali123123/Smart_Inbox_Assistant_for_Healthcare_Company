package com.smartinbox.repository;

import com.smartinbox.entity.PdfImage;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PdfImageRepository extends JpaRepository<PdfImage, Long> {
    List<PdfImage> findByAttachmentIdOrderByPageNumberAsc(Long attachmentId);
    void deleteByAttachmentId(Long attachmentId);
}
