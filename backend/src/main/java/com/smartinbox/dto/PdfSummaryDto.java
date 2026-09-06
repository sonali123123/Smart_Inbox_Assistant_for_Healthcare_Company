package com.smartinbox.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PdfSummaryDto {
    private Long id;
    private String summaryText;
    private String relevanceOpinion;
    private String relevanceReason;
}
