package com.smartinbox.dto;

import lombok.*;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class BatchStatusResponse {
    private String batchId;
    private List<DocumentStatus> documents;

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class DocumentStatus {
        private String filename;
        private String status;
        private Long durationMs;
        private String errorMessage;
        private Long messageId;
    }
}
