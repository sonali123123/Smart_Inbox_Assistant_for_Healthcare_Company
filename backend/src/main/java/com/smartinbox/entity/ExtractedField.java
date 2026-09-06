package com.smartinbox.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "EXTRACTED_FIELDS")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ExtractedField {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "message_id", nullable = false)
    @JsonIgnore
    private Message message;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "attachment_id")
    @JsonIgnore
    private Attachment attachment;

    @Column(name = "field_group", nullable = false, length = 50)
    private String fieldGroup;

    @Column(name = "field_name", nullable = false, length = 100)
    private String fieldName;

    @Lob
    @Column(name = "field_value")
    private String fieldValue;

    @Column(name = "confidence")
    private Double confidence;

    @Column(name = "source_type", length = 30)
    private String sourceType; // EMAIL or PDF_PAGE

    @Column(name = "source_ref", length = 255)
    private String sourceRef; // e.g. "email" or "attachment:55,page:2"

    @Column(name = "reviewer_edited", nullable = false)
    @Builder.Default
    private boolean reviewerEdited = false;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
