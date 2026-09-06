package com.smartinbox.repository;

import com.smartinbox.entity.Message;
import com.smartinbox.model.SourceType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface MessageRepository extends JpaRepository<Message, Long> {

    Optional<Message> findByMessageIdHeader(String messageIdHeader);

    boolean existsByMessageIdHeader(String messageIdHeader);

    List<Message> findBySourceTypeOrderByReceivedDateDesc(SourceType sourceType);

    List<Message> findAllByOrderByReceivedDateDesc();

    @Query("SELECT m FROM Message m WHERE (:sourceType IS NULL OR m.sourceType = :sourceType) ORDER BY m.receivedDate DESC")
    List<Message> findAllWithDetails(@Param("sourceType") SourceType sourceType);
}
