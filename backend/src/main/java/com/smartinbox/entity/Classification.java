package com.smartinbox.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.smartinbox.model.Category;
import com.smartinbox.model.ReviewerStatus;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "CLASSIFICATIONS")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Classification {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "message_id", nullable = false)
    @JsonIgnore
    private Message message;

    @Enumerated(EnumType.STRING)
    @Column(name = "category", nullable = false, length = 50)
    private Category category;

    @Column(name = "confidence")
    private Double confidence;

    @Column(name = "reason", length = 1000)
    private String reason;

    @Enumerated(EnumType.STRING)
    @Column(name = "reviewer_status", nullable = false, length = 30)
    @Builder.Default
    private ReviewerStatus reviewerStatus = ReviewerStatus.PENDING;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
