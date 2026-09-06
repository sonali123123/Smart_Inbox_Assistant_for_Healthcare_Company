package com.smartinbox.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "PDF_TRANSLATIONS")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PdfTranslation {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "attachment_id", nullable = false, unique = true)
    @JsonIgnore
    private Attachment attachment;

    @Column(name = "source_language", length = 50)
    private String sourceLanguage;

    @Column(name = "original_text_ref", length = 500)
    private String originalTextRef;

    @Lob
    @Column(name = "translated_text")
    private String translatedText;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
