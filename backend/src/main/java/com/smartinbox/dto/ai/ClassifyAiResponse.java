package com.smartinbox.dto.ai;

import lombok.*;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ClassifyAiResponse {
    private List<ClassificationItem> classifications;
    private SafetyReportFields safetyReportFields;
    private QualityComplaintFields qualityComplaintFields;
    private InfoRequestFields infoRequestFields;

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class ClassificationItem {
        private String category;
        private Double confidence;
        private String reason;
    }

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class FieldValue {
        private String value;
        private Double confidence;
        private String sourceRef;
    }

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class SafetyReportFields {
        private PatientFields patient;
        private ReporterFields reporter;
        private ProductFields product;
        private ReactionFields reaction;
        private SeverityFields severity;
        private FieldValue narrative;
    }

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class PatientFields {
        private FieldValue age;
        private FieldValue sex;
        private FieldValue weightHeight;
        private FieldValue relevantHistory;
    }

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class ReporterFields {
        private FieldValue name;
        private FieldValue role;
        private FieldValue country;
    }

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class ProductFields {
        private FieldValue name;
        private FieldValue dose;
        private FieldValue route;
        private FieldValue startDate;
        private FieldValue stopDate;
    }

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class ReactionFields {
        private FieldValue description;
        private FieldValue onset;
        private FieldValue outcome;
    }

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class SeverityFields {
        private FieldValue level;
    }

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class QualityComplaintFields {
        private FieldValue productBatchLot;
        private FieldValue defectDescription;
        private FieldValue photoMentioned;
    }

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class InfoRequestFields {
        private List<InfoRequestQuestion> questions;
    }

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class InfoRequestQuestion {
        private String question;
        private String productTopic;
        private Double confidence;
        private String sourceRef;
    }
}
