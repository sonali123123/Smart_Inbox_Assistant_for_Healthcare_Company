package com.smartinbox.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "PDF_SUMMARIES")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PdfSummary {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "attachment_id", nullable = false, unique = true)
    @JsonIgnore
    private Attachment attachment;

    @Lob
    @Column(name = "summary_text")
    private String summaryText;

    @Column(name = "relevance_opinion", length = 30)
    private String relevanceOpinion;

    @Column(name = "relevance_reason", length = 1000)
    private String relevanceReason;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
