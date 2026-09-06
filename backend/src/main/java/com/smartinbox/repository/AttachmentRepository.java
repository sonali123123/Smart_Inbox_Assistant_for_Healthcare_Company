package com.smartinbox.repository;

import com.smartinbox.entity.Attachment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AttachmentRepository extends JpaRepository<Attachment, Long> {
    List<Attachment> findByMessageId(Long messageId);
    List<Attachment> findByMessageIdAndIsPdfTrue(Long messageId);
}
