package com.smartinbox.controller;

import com.smartinbox.dto.AuditLogDto;
import com.smartinbox.entity.AuditLog;
import com.smartinbox.repository.AuditLogRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/audit")
@RequiredArgsConstructor
@Slf4j
public class AuditController {

    private final AuditLogRepository auditLogRepository;

    @GetMapping
    public ResponseEntity<List<AuditLogDto>> getAuditLog(
            @RequestParam(required = false) String entityType,
            @RequestParam(required = false) Long entityId
    ) {
        List<AuditLog> entries;
        if (entityType != null && entityId != null) {
            entries = auditLogRepository.findByEntityTypeAndEntityIdOrderByTimestampDesc(entityType, entityId);
        } else {
            entries = auditLogRepository.findAllByOrderByTimestampDesc();
        }

        List<AuditLogDto> dtos = entries.stream().map(e -> AuditLogDto.builder()
                .id(e.getId())
                .entityType(e.getEntityType())
                .entityId(e.getEntityId())
                .action(e.getAction())
                .actor(e.getActor().name())
                .detailsJson(e.getDetailsJson())
                .timestamp(e.getTimestamp())
                .build()).collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }
}
