package com.smartinbox.dto.ai;

import lombok.*;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ProcessDocumentAiResponse {
    private String pdfType;
    private Double ocrConfidence;
    private String extractedText;
    private List<TableData> tables;
    private List<ImageData> images;
    private TranslationData translation;
    private String summary;
    private String relevanceOpinion;
    private String relevanceReason;

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class TableData {
        private Integer page;
        private List<List<Object>> rows;
    }

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class ImageData {
        private Integer page;
        private String description;
        private boolean reviewFlag;
    }

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class TranslationData {
        private String sourceLanguage;
        private String originalTextRef;
        private String translatedText;
    }
}
