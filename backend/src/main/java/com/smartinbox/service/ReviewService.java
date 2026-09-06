package com.smartinbox.service;

import com.smartinbox.entity.Classification;
import com.smartinbox.entity.ExtractedField;
import com.smartinbox.entity.ReviewAction;
import com.smartinbox.model.Category;
import com.smartinbox.model.ReviewActionType;
import com.smartinbox.model.ReviewerStatus;
import com.smartinbox.repository.ClassificationRepository;
import com.smartinbox.repository.ExtractedFieldRepository;
import com.smartinbox.repository.ReviewActionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Slf4j
public class ReviewService {

    private final ClassificationRepository classificationRepository;
    private final ExtractedFieldRepository extractedFieldRepository;
    private final ReviewActionRepository reviewActionRepository;
    private final AuditService auditService;

    @Transactional
    public Classification reviewClassification(Long classificationId, String actionStr, String newCategoryStr, String reviewerName) {
        Classification classification = classificationRepository.findById(classificationId)
                .orElseThrow(() -> new IllegalArgumentException("Classification not found: " + classificationId));

        ReviewActionType actionType = ReviewActionType.valueOf(actionStr.toUpperCase());
        String prevCategory = classification.getCategory().name();

        if (actionType == ReviewActionType.ACCEPT) {
            classification.setReviewerStatus(ReviewerStatus.ACCEPTED);
        } else if (actionType == ReviewActionType.OVERRIDE) {
            classification.setReviewerStatus(ReviewerStatus.OVERRIDDEN);
            if (newCategoryStr != null && !newCategoryStr.isBlank()) {
                Category newCat = Category.valueOf(newCategoryStr.toUpperCase());
                classification.setCategory(newCat);
            }
        }
        classification = classificationRepository.save(classification);

        // Record Review Action
        ReviewAction action = ReviewAction.builder()
                .message(classification.getMessage())
                .reviewerName(reviewerName != null && !reviewerName.isBlank() ? reviewerName : "Reviewer")
                .action(actionType)
                .targetRef("classification:" + classification.getId())
                .previousValue(prevCategory)
                .newValue(classification.getCategory().name())
                .build();
        reviewActionRepository.save(action);

        auditService.logReviewerAction(
                "CLASSIFICATION",
                classification.getId(),
                actionType.name(),
                reviewerName != null ? reviewerName : "Reviewer",
                "Changed from " + prevCategory + " to " + classification.getCategory().name()
        );

        return classification;
    }

    @Transactional
    public ExtractedField editField(Long fieldId, String newValue, String reviewerName, String reason) {
        ExtractedField field = extractedFieldRepository.findById(fieldId)
                .orElseThrow(() -> new IllegalArgumentException("Field not found: " + fieldId));

        String prevValue = field.getFieldValue();
        field.setFieldValue(newValue);
        field.setReviewerEdited(true);
        field = extractedFieldRepository.save(field);

        String target = "field:" + field.getId() + ":" + field.getFieldName();
        if (reason != null && !reason.isBlank()) {
            target += " [Reason: " + reason.trim() + "]";
        }

        // Record Review Action
        ReviewAction action = ReviewAction.builder()
                .message(field.getMessage())
                .reviewerName(reviewerName != null && !reviewerName.isBlank() ? reviewerName : "Reviewer")
                .action(ReviewActionType.EDIT)
                .targetRef(target)
                .previousValue(prevValue)
                .newValue(newValue)
                .build();
        reviewActionRepository.save(action);

        auditService.logReviewerAction(
                "EXTRACTED_FIELD",
                field.getId(),
                "EDIT",
                reviewerName != null ? reviewerName : "Reviewer",
                "Field " + field.getFieldName() + " updated" + (reason != null && !reason.isBlank() ? " (" + reason.trim() + ")" : "")
        );

        return field;
    }

    @Transactional
    public ExtractedField editField(Long fieldId, String newValue, String reviewerName) {
        return editField(fieldId, newValue, reviewerName, null);
    }
}
