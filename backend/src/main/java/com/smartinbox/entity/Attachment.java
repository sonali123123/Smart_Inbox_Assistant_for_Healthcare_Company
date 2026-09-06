package com.smartinbox.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.smartinbox.model.PdfType;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "ATTACHMENTS")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Attachment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "message_id", nullable = false)
    @JsonIgnore
    private Message message;

    @Column(name = "filename", nullable = false, length = 255)
    private String filename;

    @Column(name = "content_type", length = 100)
    private String contentType;

    @Column(name = "is_pdf", nullable = false)
    @Builder.Default
    private boolean isPdf = true;

    @Column(name = "storage_path", length = 1000)
    private String storagePath;

    @Enumerated(EnumType.STRING)
    @Column(name = "pdf_type", length = 30)
    private PdfType pdfType;

    @Column(name = "logged_only", nullable = false)
    @Builder.Default
    private boolean loggedOnly = false;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @OneToOne(mappedBy = "attachment", cascade = CascadeType.ALL, orphanRemoval = true)
    private PdfSummary summary;

    @OneToMany(mappedBy = "attachment", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<PdfTable> tables = new ArrayList<>();

    @OneToMany(mappedBy = "attachment", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<PdfImage> images = new ArrayList<>();

    @OneToOne(mappedBy = "attachment", cascade = CascadeType.ALL, orphanRemoval = true)
    private PdfTranslation translation;
}
