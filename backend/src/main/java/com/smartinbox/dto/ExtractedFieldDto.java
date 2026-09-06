package com.smartinbox.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ExtractedFieldDto {
    private Long id;
    private Long attachmentId;
    private String fieldGroup;
    private String fieldName;
    private String fieldValue;
    private Double confidence;
    private String sourceType;
    private String sourceRef;
    private boolean reviewerEdited;
}
