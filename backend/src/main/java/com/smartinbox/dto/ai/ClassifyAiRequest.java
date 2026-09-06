package com.smartinbox.dto.ai;

import lombok.*;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ClassifyAiRequest {
    private String emailBody;
    private String sender;
    private String subject;
    private List<PdfExtractionItem> pdfExtractions;

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class PdfExtractionItem {
        private Long attachmentId;
        private String extractedText;
        private List<Object> tables;
    }
}
