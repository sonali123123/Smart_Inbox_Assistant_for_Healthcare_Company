package com.smartinbox.service;

import com.smartinbox.entity.Classification;
import com.smartinbox.entity.ExtractedField;
import com.smartinbox.entity.Message;
import com.smartinbox.entity.ReviewAction;
import com.smartinbox.model.Category;
import com.smartinbox.model.ReviewActionType;
import com.smartinbox.model.ReviewerStatus;
import com.smartinbox.repository.ClassificationRepository;
import com.smartinbox.repository.ExtractedFieldRepository;
import com.smartinbox.repository.ReviewActionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
public class ReviewServiceTest {

    @Mock
    private ClassificationRepository classificationRepository;

    @Mock
    private ExtractedFieldRepository extractedFieldRepository;

    @Mock
    private ReviewActionRepository reviewActionRepository;

    @Mock
    private AuditService auditService;

    @InjectMocks
    private ReviewService reviewService;

    private Message message;
    private Classification classification;
    private ExtractedField field;

    @BeforeEach
    void setUp() {
        message = Message.builder().id(1L).subject("Test Subject").build();

        classification = Classification.builder()
                .id(10L)
                .message(message)
                .category(Category.SAFETY_REPORT)
                .confidence(0.92)
                .reason("Test reason")
                .reviewerStatus(ReviewerStatus.PENDING)
                .build();

        field = ExtractedField.builder()
                .id(20L)
                .message(message)
                .fieldGroup("PATIENT")
                .fieldName("age")
                .fieldValue("55")
                .confidence(0.85)
                .sourceType("EMAIL")
                .sourceRef("email")
                .reviewerEdited(false)
                .build();
    }

    @Test
    void testAcceptClassification() {
        when(classificationRepository.findById(10L)).thenReturn(Optional.of(classification));
        when(classificationRepository.save(any(Classification.class))).thenAnswer(i -> i.getArgument(0));

        Classification result = reviewService.reviewClassification(10L, "ACCEPT", null, "Dr. Reviewer");

        assertEquals(ReviewerStatus.ACCEPTED, result.getReviewerStatus());
        assertEquals(Category.SAFETY_REPORT, result.getCategory());
        verify(reviewActionRepository).save(any(ReviewAction.class));
        verify(auditService).logReviewerAction(eq("CLASSIFICATION"), eq(10L), eq("ACCEPT"), eq("Dr. Reviewer"), any());
    }

    @Test
    void testOverrideClassification() {
        when(classificationRepository.findById(10L)).thenReturn(Optional.of(classification));
        when(classificationRepository.save(any(Classification.class))).thenAnswer(i -> i.getArgument(0));

        Classification result = reviewService.reviewClassification(10L, "OVERRIDE", "QUALITY_COMPLAINT", "Dr. Reviewer");

        assertEquals(ReviewerStatus.OVERRIDDEN, result.getReviewerStatus());
        assertEquals(Category.QUALITY_COMPLAINT, result.getCategory());
        verify(reviewActionRepository).save(any(ReviewAction.class));
        verify(auditService).logReviewerAction(eq("CLASSIFICATION"), eq(10L), eq("OVERRIDE"), eq("Dr. Reviewer"), any());
    }

    @Test
    void testEditField() {
        when(extractedFieldRepository.findById(20L)).thenReturn(Optional.of(field));
        when(extractedFieldRepository.save(any(ExtractedField.class))).thenAnswer(i -> i.getArgument(0));

        ExtractedField result = reviewService.editField(20L, "58", "Dr. Reviewer");

        assertEquals("58", result.getFieldValue());
        assertTrue(result.isReviewerEdited());
        verify(reviewActionRepository).save(any(ReviewAction.class));
        verify(auditService).logReviewerAction(eq("EXTRACTED_FIELD"), eq(20L), eq("EDIT"), eq("Dr. Reviewer"), any());
    }

    @Test
    void testEditFieldWithReason() {
        when(extractedFieldRepository.findById(20L)).thenReturn(Optional.of(field));
        when(extractedFieldRepository.save(any(ExtractedField.class))).thenAnswer(i -> i.getArgument(0));

        ExtractedField result = reviewService.editField(20L, "60", "Dr. Reviewer", "Corrected per hospital discharge summary");

        assertEquals("60", result.getFieldValue());
        assertTrue(result.isReviewerEdited());
        verify(reviewActionRepository).save(argThat(action ->
            action.getTargetRef() != null && action.getTargetRef().contains("[Reason: Corrected per hospital discharge summary]")
        ));
        verify(auditService).logReviewerAction(eq("EXTRACTED_FIELD"), eq(20L), eq("EDIT"), eq("Dr. Reviewer"), any());
    }
}
