package com.smartinbox.repository;

import com.smartinbox.entity.PdfTable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PdfTableRepository extends JpaRepository<PdfTable, Long> {
    List<PdfTable> findByAttachmentIdOrderByPageNumberAsc(Long attachmentId);
    void deleteByAttachmentId(Long attachmentId);
}
