package com.smartinbox.controller;

import com.smartinbox.service.MailIngestionService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/mail")
@RequiredArgsConstructor
@Slf4j
public class MailController {

    private final MailIngestionService mailIngestionService;

    @PostMapping("/ingest")
    public ResponseEntity<Map<String, Object>> triggerIngest() {
        log.info("Received request to trigger manual mailbox ingestion");
        int count = mailIngestionService.ingestMails();
        return ResponseEntity.ok(Map.of(
                "status", "SUCCESS",
                "messagesIngested", count,
                "message", "Ingestion completed. " + count + " new messages enqueued for processing."
        ));
    }
}
