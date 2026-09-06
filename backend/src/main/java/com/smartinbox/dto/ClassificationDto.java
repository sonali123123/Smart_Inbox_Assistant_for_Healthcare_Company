package com.smartinbox.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ClassificationDto {
    private Long id;
    private String category;
    private Double confidence;
    private String reason;
    private String reviewerStatus;
}
