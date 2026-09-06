package com.smartinbox.dto.ai;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ProcessDocumentAiRequest {
    private String pdfBase64;
    private String filename;
    private EmailContext emailContext;

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class EmailContext {
        private String subject;
        private String bodySnippet;
    }
}
