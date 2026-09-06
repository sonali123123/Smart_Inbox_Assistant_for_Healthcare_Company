package com.smartinbox.controller;

import com.smartinbox.dto.ClassificationDto;
import com.smartinbox.dto.ExtractedFieldDto;
import com.smartinbox.dto.FieldEditRequest;
import com.smartinbox.dto.ReviewRequest;
import com.smartinbox.entity.Classification;
import com.smartinbox.entity.ExtractedField;
import com.smartinbox.service.ReviewService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/messages")
@RequiredArgsConstructor
@Slf4j
public class ReviewController {

    private final ReviewService reviewService;

    @PutMapping("/{id}/classifications/{classificationId}/review")
    public ResponseEntity<ClassificationDto> reviewClassification(
            @PathVariable Long id,
            @PathVariable Long classificationId,
            @RequestBody ReviewRequest request
    ) {
        log.info("Review action on message {} classification {}: action={} newCategory={} by={}",
                id, classificationId, request.getAction(), request.getNewCategory(), request.getReviewerName());

        Classification updated = reviewService.reviewClassification(
                classificationId,
                request.getAction(),
                request.getNewCategory(),
                request.getReviewerName()
        );

        return ResponseEntity.ok(ClassificationDto.builder()
                .id(updated.getId())
                .category(updated.getCategory().name())
                .confidence(updated.getConfidence())
                .reason(updated.getReason())
                .reviewerStatus(updated.getReviewerStatus().name())
                .build());
    }

    @PutMapping("/{id}/fields/{fieldId}")
    public ResponseEntity<ExtractedFieldDto> editField(
            @PathVariable Long id,
            @PathVariable Long fieldId,
            @RequestBody FieldEditRequest request
    ) {
        log.info("Field edit on message {} field {}: newValue='{}' by={} reason='{}'",
                id, fieldId, request.getNewValue(), request.getReviewerName(), request.getReason());

        ExtractedField updated = reviewService.editField(
                fieldId,
                request.getNewValue(),
                request.getReviewerName(),
                request.getReason()
        );

        return ResponseEntity.ok(ExtractedFieldDto.builder()
                .id(updated.getId())
                .attachmentId(updated.getAttachment() != null ? updated.getAttachment().getId() : null)
                .fieldGroup(updated.getFieldGroup())
                .fieldName(updated.getFieldName())
                .fieldValue(updated.getFieldValue())
                .confidence(updated.getConfidence())
                .sourceType(updated.getSourceType())
                .sourceRef(updated.getSourceRef())
                .reviewerEdited(updated.isReviewerEdited())
                .build());
    }
}
