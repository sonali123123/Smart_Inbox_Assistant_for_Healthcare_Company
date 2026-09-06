package com.smartinbox.repository;

import com.smartinbox.entity.ExtractedField;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ExtractedFieldRepository extends JpaRepository<ExtractedField, Long> {
    List<ExtractedField> findByMessageId(Long messageId);
    List<ExtractedField> findByMessageIdAndFieldGroup(Long messageId, String fieldGroup);
    void deleteByMessageId(Long messageId);
}
