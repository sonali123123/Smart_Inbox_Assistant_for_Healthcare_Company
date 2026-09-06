package com.smartinbox.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "LITERATURE_CASES")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class LiteratureCase {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "batch_id", nullable = false, length = 100)
    private String batchId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "message_id", nullable = false)
    @JsonIgnore
    private Message message;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "source_attachment_id", nullable = false)
    @JsonIgnore
    private Attachment sourceAttachment;

    @Column(name = "case_index", nullable = false)
    @Builder.Default
    private Integer caseIndex = 1;

    @Column(name = "is_reportable", nullable = false)
    @Builder.Default
    private boolean isReportable = true;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
