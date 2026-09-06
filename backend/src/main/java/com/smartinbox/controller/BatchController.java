package com.smartinbox.controller;

import com.smartinbox.dto.BatchRunRequest;
import com.smartinbox.dto.BatchStatusResponse;
import com.smartinbox.service.BatchService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/batch")
@RequiredArgsConstructor
@Slf4j
public class BatchController {

    private final BatchService batchService;

    @PostMapping("/run")
    public ResponseEntity<Map<String, String>> runBatch(@RequestBody BatchRunRequest request) {
        String dir = request.getSourceDir() != null && !request.getSourceDir().isBlank()
                ? request.getSourceDir()
                : "test-data/emails";

        log.info("Batch run requested for directory: {}", dir);
        String batchId = batchService.runBatch(dir);
        return ResponseEntity.ok(Map.of("batchId", batchId));
    }

    @GetMapping("/{batchId}/status")
    public ResponseEntity<BatchStatusResponse> getBatchStatus(@PathVariable String batchId) {
        BatchStatusResponse status = batchService.getBatchStatus(batchId);
        return ResponseEntity.ok(status);
    }
}
