package com.smartinbox.dto.ai;

import lombok.*;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class LiteratureSplitAiResponse {
    private String filename;
    private List<LiteratureCaseItem> cases;

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class LiteratureCaseItem {
        private Integer caseIndex;
        @com.fasterxml.jackson.annotation.JsonProperty("isReportable")
        private Boolean isReportable;
        private String summary;
        private String relevanceReason;
        private ClassifyAiResponse.SafetyReportFields safetyReportFields;

        public Boolean isReportable() {
            return Boolean.TRUE.equals(this.isReportable);
        }
    }
}
