package com.smartinbox.controller;

import com.smartinbox.entity.Attachment;
import com.smartinbox.repository.AttachmentRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.File;

@RestController
@RequestMapping("/api/attachments")
@RequiredArgsConstructor
@Slf4j
public class AttachmentController {

    private final AttachmentRepository attachmentRepository;

    @GetMapping("/{id}/file")
    public ResponseEntity<Resource> streamAttachmentFile(@PathVariable Long id) {
        Attachment attachment = attachmentRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Attachment not found: " + id));

        if (attachment.getStoragePath() == null) {
            return ResponseEntity.notFound().build();
        }

        File file = new File(attachment.getStoragePath());
        if (!file.exists()) {
            File fallback = new File("..", attachment.getStoragePath());
            if (fallback.exists()) {
                file = fallback;
            } else {
                log.warn("File on disk not found: {}", attachment.getStoragePath());
                return ResponseEntity.notFound().build();
            }
        }

        Resource resource = new FileSystemResource(file);
        String contentType = attachment.getContentType() != null && !attachment.getContentType().isBlank()
                ? attachment.getContentType()
                : "application/pdf";

        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(contentType))
                .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + attachment.getFilename() + "\"")
                .body(resource);
    }
}
