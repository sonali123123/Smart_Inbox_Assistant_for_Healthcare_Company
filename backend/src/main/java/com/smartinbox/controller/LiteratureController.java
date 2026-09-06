package com.smartinbox.controller;

import com.smartinbox.dto.MessageListItemDto;
import com.smartinbox.entity.Classification;
import com.smartinbox.entity.LiteratureCase;
import com.smartinbox.entity.Message;
import com.smartinbox.model.ReviewerStatus;
import com.smartinbox.repository.ClassificationRepository;
import com.smartinbox.repository.LiteratureCaseRepository;
import com.smartinbox.service.LiteratureService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/literature")
@RequiredArgsConstructor
@Slf4j
public class LiteratureController {

    private final LiteratureService literatureService;
    private final LiteratureCaseRepository literatureCaseRepository;
    private final ClassificationRepository classificationRepository;

    @PostMapping(value = "/batch", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Map<String, String>> uploadLiteratureBatch(
            @RequestParam("files") List<MultipartFile> files
    ) {
        log.info("Received literature batch upload with {} files", files.size());
        String batchId = literatureService.processLiteratureBatch(files);
        return ResponseEntity.ok(Map.of("batchId", batchId));
    }

    @GetMapping("/batch/{batchId}")
    @Transactional(readOnly = true)
    public ResponseEntity<Map<String, Object>> getLiteratureBatchCases(@PathVariable String batchId) {
        List<LiteratureCase> cases = literatureCaseRepository.findByBatchIdOrderByCaseIndexAsc(batchId);
        List<MessageListItemDto> items = new ArrayList<>();

        for (LiteratureCase lc : cases) {
            Message m = lc.getMessage();
            List<Classification> classifications = classificationRepository.findByMessageId(m.getId());

            boolean hasPending = classifications.stream()
                    .anyMatch(c -> c.getReviewerStatus() == ReviewerStatus.PENDING);
            String derivedStatus = hasPending ? "PENDING_REVIEW" : "REVIEWED";

            items.add(MessageListItemDto.builder()
                    .id(m.getId())
                    .sourceType(m.getSourceType().name())
                    .sender(m.getSender())
                    .subject(m.getSubject())
                    .receivedDate(m.getReceivedDate())
                    .classifications(classifications.stream().map(c -> com.smartinbox.dto.ClassificationDto.builder()
                            .id(c.getId())
                            .category(c.getCategory().name())
                            .confidence(c.getConfidence())
                            .reason(c.getReason())
                            .reviewerStatus(c.getReviewerStatus().name())
                            .build()).collect(Collectors.toList()))
                    .topSummary(m.getBodyText())
                    .status(derivedStatus)
                    .attachmentCount(1)
                    .build());
        }

        return ResponseEntity.ok(Map.of(
                "batchId", batchId,
                "totalCases", items.size(),
                "cases", items
        ));
    }
}
