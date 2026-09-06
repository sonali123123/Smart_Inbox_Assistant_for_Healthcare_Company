package com.smartinbox.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.smartinbox.entity.AuditLog;
import com.smartinbox.model.ActorType;
import com.smartinbox.repository.AuditLogRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Slf4j
public class AuditService {

    private final AuditLogRepository auditLogRepository;
    private final ObjectMapper objectMapper;

    @Transactional
    public void logAiDecision(String entityType, Long entityId, String action, Object details) {
        String detailsJson = serialize(details);
        AuditLog entry = AuditLog.builder()
                .entityType(entityType)
                .entityId(entityId)
                .action(action)
                .actor(ActorType.AI)
                .detailsJson(detailsJson)
                .build();
        auditLogRepository.save(entry);
        log.info("Audit logged [AI] entity={} id={} action={}", entityType, entityId, action);
    }

    @Transactional
    public void logReviewerAction(String entityType, Long entityId, String action, String reviewerName, Object details) {
        String detailsJson = serialize(details);
        AuditLog entry = AuditLog.builder()
                .entityType(entityType)
                .entityId(entityId)
                .action(action + " (by " + reviewerName + ")")
                .actor(ActorType.REVIEWER)
                .detailsJson(detailsJson)
                .build();
        auditLogRepository.save(entry);
        log.info("Audit logged [REVIEWER: {}] entity={} id={} action={}", reviewerName, entityType, entityId, action);
    }

    private String serialize(Object obj) {
        if (obj == null) return null;
        if (obj instanceof String) return (String) obj;
        try {
            return objectMapper.writeValueAsString(obj);
        } catch (Exception e) {
            log.warn("Failed to serialize audit log details: {}", e.getMessage());
            return String.valueOf(obj);
        }
    }
}
