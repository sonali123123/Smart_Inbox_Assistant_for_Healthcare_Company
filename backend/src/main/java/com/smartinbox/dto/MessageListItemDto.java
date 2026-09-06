package com.smartinbox.dto;

import lombok.*;
import java.time.LocalDateTime;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class MessageListItemDto {
    private Long id;
    private String sourceType;
    private String sender;
    private String subject;
    private LocalDateTime receivedDate;
    private List<ClassificationDto> classifications;
    private String topSummary;
    private String status; // PENDING_REVIEW | REVIEWED
    private int attachmentCount;
}
