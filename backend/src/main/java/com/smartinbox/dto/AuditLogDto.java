package com.smartinbox.dto;

import lombok.*;
import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AuditLogDto {
    private Long id;
    private String entityType;
    private Long entityId;
    private String action;
    private String actor;
    private String detailsJson;
    private LocalDateTime timestamp;
}
