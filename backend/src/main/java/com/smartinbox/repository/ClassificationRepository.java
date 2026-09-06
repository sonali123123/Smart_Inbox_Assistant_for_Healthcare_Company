package com.smartinbox.repository;

import com.smartinbox.entity.Classification;
import com.smartinbox.model.Category;
import com.smartinbox.model.ReviewerStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ClassificationRepository extends JpaRepository<Classification, Long> {
    List<Classification> findByMessageId(Long messageId);
    List<Classification> findByCategory(Category category);
    List<Classification> findByReviewerStatus(ReviewerStatus reviewerStatus);
    void deleteByMessageId(Long messageId);
}
