package com.smartinbox.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "PDF_IMAGES")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PdfImage {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "attachment_id", nullable = false)
    @JsonIgnore
    private Attachment attachment;

    @Column(name = "page_number")
    private Integer pageNumber;

    @Column(name = "description", length = 1000)
    private String description;

    @Column(name = "review_flag", nullable = false)
    @Builder.Default
    private boolean reviewFlag = false;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
