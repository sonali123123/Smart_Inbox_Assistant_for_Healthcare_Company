package com.smartinbox.repository;

import com.smartinbox.entity.ReviewAction;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ReviewActionRepository extends JpaRepository<ReviewAction, Long> {
    List<ReviewAction> findByMessageIdOrderByTimestampDesc(Long messageId);
}
