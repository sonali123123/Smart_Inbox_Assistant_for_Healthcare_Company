package com.smartinbox.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.smartinbox.dto.ai.*;
import com.smartinbox.entity.*;
import com.smartinbox.model.Category;
import com.smartinbox.model.PdfType;
import com.smartinbox.repository.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
import org.mockito.junit.jupiter.MockitoExtension;

import java.io.File;
import java.io.FileOutputStream;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
public class DocumentProcessingServiceTest {

    @Mock
    private AiServiceClient aiServiceClient;

    @Mock
    private AuditService auditService;

    @Mock
    private MessageRepository messageRepository;

    @Mock
    private AttachmentRepository attachmentRepository;

    @Mock
    private PdfSummaryRepository pdfSummaryRepository;

    @Mock
    private PdfTableRepository pdfTableRepository;

    @Mock
    private PdfImageRepository pdfImageRepository;

    @Mock
    private PdfTranslationRepository pdfTranslationRepository;

    @Mock
    private ClassificationRepository classificationRepository;

    @Mock
    private ExtractedFieldRepository extractedFieldRepository;

    @Spy
    private ObjectMapper objectMapper = new ObjectMapper();

    @InjectMocks
    private DocumentProcessingService documentProcessingService;

    private Message message;
    private Attachment pdfAttachment;
    private File tempPdfFile;

    @BeforeEach
    void setUp() throws Exception {
        tempPdfFile = File.createTempFile("test_sample", ".pdf");
        try (FileOutputStream fos = new FileOutputStream(tempPdfFile)) {
            fos.write("%PDF-1.4 dummy content".getBytes());
        }

        message = Message.builder()
                .id(100L)
                .sender("physician@hospital.org")
                .subject("Adverse Reaction Report")
                .bodyText("Patient had a severe rash.")
                .build();

        pdfAttachment = Attachment.builder()
                .id(55L)
                .message(message)
                .filename("form_report.pdf")
                .isPdf(true)
                .loggedOnly(false)
                .storagePath(tempPdfFile.getAbsolutePath())
                .build();
    }

    @Test
    void testProcessMessageEndToEndOrchestration() throws Exception {
        when(messageRepository.findById(100L)).thenReturn(Optional.of(message));
        when(attachmentRepository.findByMessageId(100L)).thenReturn(List.of(pdfAttachment));

        // Mock 1st call: POST /ai/process-document
        ProcessDocumentAiResponse docResponse = ProcessDocumentAiResponse.builder()
                .pdfType("SCANNED")
                .ocrConfidence(0.85)
                .extractedText("Patient: John Doe, Drug: CardioFix, Event: Anaphylaxis")
                .tables(List.of(ProcessDocumentAiResponse.TableData.builder()
                        .page(1)
                        .rows(List.of(List.of("Test", "Result"), List.of("WBC", "10.5")))
                        .build()))
                .images(List.of(ProcessDocumentAiResponse.ImageData.builder()
                        .page(1)
                        .description("Photo of rash on arm")
                        .reviewFlag(true)
                        .build()))
                .summary("This document details an adverse event case.")
                .relevanceOpinion("RELEVANT")
                .relevanceReason("Specific patient and drug mentioned")
                .build();
        when(aiServiceClient.processDocument(any())).thenReturn(docResponse);

        // Mock 2nd call: POST /ai/classify-and-extract
        ClassifyAiResponse classifyResponse = ClassifyAiResponse.builder()
                .classifications(List.of(
                        ClassifyAiResponse.ClassificationItem.builder()
                                .category("SAFETY_REPORT")
                                .confidence(0.95)
                                .reason("All 4 safety report criteria met")
                                .build(),
                        ClassifyAiResponse.ClassificationItem.builder()
                                .category("QUALITY_COMPLAINT")
                                .confidence(0.60)
                                .reason("Packaging seal issue noted")
                                .build()
                ))
                .safetyReportFields(ClassifyAiResponse.SafetyReportFields.builder()
                        .patient(ClassifyAiResponse.PatientFields.builder()
                                .age(ClassifyAiResponse.FieldValue.builder().value("54").confidence(0.9).sourceRef("attachment:55,page:1").build())
                                .sex(ClassifyAiResponse.FieldValue.builder().value("Not stated").confidence(null).sourceRef(null).build())
                                .weightHeight(ClassifyAiResponse.FieldValue.builder().value("Not stated").confidence(null).sourceRef(null).build())
                                .relevantHistory(ClassifyAiResponse.FieldValue.builder().value("Not stated").confidence(null).sourceRef(null).build())
                                .build())
                        .reporter(ClassifyAiResponse.ReporterFields.builder()
                                .name(ClassifyAiResponse.FieldValue.builder().value("Dr. Smith").confidence(0.92).sourceRef("email").build())
                                .role(ClassifyAiResponse.FieldValue.builder().value("Physician").confidence(0.9).sourceRef("email").build())
                                .country(ClassifyAiResponse.FieldValue.builder().value("USA").confidence(0.85).sourceRef("email").build())
                                .build())
                        .product(ClassifyAiResponse.ProductFields.builder()
                                .name(ClassifyAiResponse.FieldValue.builder().value("CardioFix").confidence(0.98).sourceRef("attachment:55,page:1").build())
                                .dose(ClassifyAiResponse.FieldValue.builder().value("20mg").confidence(0.95).sourceRef("attachment:55,page:1").build())
                                .route(ClassifyAiResponse.FieldValue.builder().value("Oral").confidence(0.9).sourceRef("attachment:55,page:1").build())
                                .startDate(ClassifyAiResponse.FieldValue.builder().value("2026-08-01").confidence(0.88).sourceRef("attachment:55,page:1").build())
                                .stopDate(ClassifyAiResponse.FieldValue.builder().value("Not stated").confidence(null).sourceRef(null).build())
                                .build())
                        .reaction(ClassifyAiResponse.ReactionFields.builder()
                                .description(ClassifyAiResponse.FieldValue.builder().value("Anaphylaxis").confidence(0.95).sourceRef("attachment:55,page:1").build())
                                .onset(ClassifyAiResponse.FieldValue.builder().value("1 hour").confidence(0.85).sourceRef("attachment:55,page:1").build())
                                .outcome(ClassifyAiResponse.FieldValue.builder().value("Resolved").confidence(0.88).sourceRef("attachment:55,page:1").build())
                                .build())
                        .severity(ClassifyAiResponse.SeverityFields.builder()
                                .level(ClassifyAiResponse.FieldValue.builder().value("Hospitalization").confidence(0.9).sourceRef("email").build())
                                .build())
                        .narrative(ClassifyAiResponse.FieldValue.builder()
                                .value("A 54-year-old patient experienced anaphylaxis after taking CardioFix.")
                                .confidence(0.9)
                                .sourceRef("email")
                                .build())
                        .build())
                .build();
        when(aiServiceClient.classifyAndExtract(any())).thenReturn(classifyResponse);

        // Execute orchestration
        documentProcessingService.processMessage(100L);

        // 1. Verify exactly 1 call per PDF and exactly 1 call for classification (Max 2 calls rule)
        verify(aiServiceClient, times(1)).processDocument(any());
        verify(aiServiceClient, times(1)).classifyAndExtract(any());

        // 2. Verify attachment updated with detected PDF type
        verify(attachmentRepository).save(argThat(a -> a.getPdfType() == PdfType.SCANNED));

        // 3. Verify PDF summary saved
        verify(pdfSummaryRepository).save(argThat(s ->
                s.getRelevanceOpinion().equals("RELEVANT") &&
                s.getSummaryText().contains("adverse event")
        ));

        // 4. Verify structured tables saved (not flattened)
        verify(pdfTableRepository).save(argThat(t ->
                t.getTableJson().contains("WBC") && t.getTableJson().contains("10.5")
        ));

        // 5. Verify image saved with review flag
        verify(pdfImageRepository).save(argThat(img ->
                img.isReviewFlag() && img.getDescription().contains("Photo of rash")
        ));

        // 6. Verify multi-label classifications saved
        ArgumentCaptor<Classification> classCaptor = ArgumentCaptor.forClass(Classification.class);
        verify(classificationRepository, times(2)).save(classCaptor.capture());
        List<Classification> savedClasses = classCaptor.getAllValues();
        assertTrue(savedClasses.stream().anyMatch(c -> c.getCategory() == Category.SAFETY_REPORT));
        assertTrue(savedClasses.stream().anyMatch(c -> c.getCategory() == Category.QUALITY_COMPLAINT));

        // 7. Verify extracted fields saved with confidence and sourceRef
        ArgumentCaptor<ExtractedField> fieldCaptor = ArgumentCaptor.forClass(ExtractedField.class);
        verify(extractedFieldRepository, atLeast(10)).save(fieldCaptor.capture());
        List<ExtractedField> savedFields = fieldCaptor.getAllValues();

        // Check age was extracted with sourceRef
        ExtractedField ageField = savedFields.stream().filter(f -> f.getFieldName().equals("age")).findFirst().orElse(null);
        assertNotNull(ageField);
        assertEquals("54", ageField.getFieldValue());
        assertEquals("attachment:55,page:1", ageField.getSourceRef());
        assertEquals("PDF_PAGE", ageField.getSourceType());

        // Check sex was marked "Not stated" with null confidence (Hard stop rule)
        ExtractedField sexField = savedFields.stream().filter(f -> f.getFieldName().equals("sex")).findFirst().orElse(null);
        assertNotNull(sexField);
        assertEquals("Not stated", sexField.getFieldValue());
        assertNull(sexField.getConfidence());

        // Clean up temp file
        if (tempPdfFile.exists()) tempPdfFile.delete();
    }
}
