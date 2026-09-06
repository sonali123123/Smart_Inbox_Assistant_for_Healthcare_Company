package com.smartinbox.service;

import com.smartinbox.config.AppProperties;
import com.smartinbox.dto.ai.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Service
@RequiredArgsConstructor
@Slf4j
public class AiServiceClient {

    private final RestTemplate restTemplate;
    private final AppProperties appProperties;

    public ProcessDocumentAiResponse processDocument(ProcessDocumentAiRequest request) {
        String url = appProperties.getAiService().getUrl() + "/ai/process-document";
        log.info("Calling AI service to process PDF: {} at {}", request.getFilename(), url);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<ProcessDocumentAiRequest> entity = new HttpEntity<>(request, headers);

        for (int attempt = 1; attempt <= 2; attempt++) {
            try {
                ResponseEntity<ProcessDocumentAiResponse> response = restTemplate.postForEntity(url, entity, ProcessDocumentAiResponse.class);
                if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                    return response.getBody();
                }
                throw new RuntimeException("AI service returned status: " + response.getStatusCode());
            } catch (Exception e) {
                if (attempt < 2) {
                    log.warn("Attempt {} failed for processDocument ({}): {}. Retrying in 1s...", attempt, request.getFilename(), e.getMessage());
                    try { Thread.sleep(1000); } catch (InterruptedException ignored) {}
                } else {
                    log.error("Failed to process document with AI service after retries: {}", e.getMessage(), e);
                    throw new RuntimeException("AI service document processing failed: " + e.getMessage(), e);
                }
            }
        }
        throw new RuntimeException("AI service document processing failed unexpectedly");
    }

    public ClassifyAiResponse classifyAndExtract(ClassifyAiRequest request) {
        String url = appProperties.getAiService().getUrl() + "/ai/classify-and-extract";
        log.info("Calling AI service to classify message: subject='{}' at {}", request.getSubject(), url);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<ClassifyAiRequest> entity = new HttpEntity<>(request, headers);

        for (int attempt = 1; attempt <= 2; attempt++) {
            try {
                ResponseEntity<ClassifyAiResponse> response = restTemplate.postForEntity(url, entity, ClassifyAiResponse.class);
                if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                    return response.getBody();
                }
                throw new RuntimeException("AI service returned status: " + response.getStatusCode());
            } catch (Exception e) {
                if (attempt < 2) {
                    log.warn("Attempt {} failed for classifyAndExtract ('{}'): {}. Retrying in 1s...", attempt, request.getSubject(), e.getMessage());
                    try { Thread.sleep(1000); } catch (InterruptedException ignored) {}
                } else {
                    log.error("Failed to classify and extract with AI service after retries: {}", e.getMessage(), e);
                    throw new RuntimeException("AI service classification failed: " + e.getMessage(), e);
                }
            }
        }
        throw new RuntimeException("AI service classification failed unexpectedly");
    }

    public LiteratureSplitAiResponse splitLiteratureCases(LiteratureSplitAiRequest request) {
        String url = appProperties.getAiService().getUrl() + "/ai/literature-case-split";
        log.info("Calling AI service to split literature cases: {} at {}", request.getFilename(), url);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<LiteratureSplitAiRequest> entity = new HttpEntity<>(request, headers);

        for (int attempt = 1; attempt <= 2; attempt++) {
            try {
                ResponseEntity<LiteratureSplitAiResponse> response = restTemplate.postForEntity(url, entity, LiteratureSplitAiResponse.class);
                if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                    return response.getBody();
                }
                throw new RuntimeException("AI service returned status: " + response.getStatusCode());
            } catch (Exception e) {
                if (attempt < 2) {
                    log.warn("Attempt {} failed for splitLiteratureCases ({}): {}. Retrying in 1s...", attempt, request.getFilename(), e.getMessage());
                    try { Thread.sleep(1000); } catch (InterruptedException ignored) {}
                } else {
                    log.error("Failed to split literature cases with AI service after retries: {}", e.getMessage(), e);
                    throw new RuntimeException("AI service literature split failed: " + e.getMessage(), e);
                }
            }
        }
        throw new RuntimeException("AI service literature split failed unexpectedly");
    }
}
