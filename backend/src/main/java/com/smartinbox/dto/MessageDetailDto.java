package com.smartinbox.dto;

import lombok.*;
import java.time.LocalDateTime;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class MessageDetailDto {
    private Long id;
    private String sourceType;
    private String sender;
    private String subject;
    private LocalDateTime receivedDate;
    private String bodyText;
    private String messageIdHeader;
    private LocalDateTime createdAt;
    private String status; // PENDING_REVIEW | REVIEWED
    private List<ClassificationDto> classifications;
    private List<AttachmentDto> attachments;
    private List<ExtractedFieldDto> extractedFields;
    private List<ReviewActionDto> reviewActions;
}
