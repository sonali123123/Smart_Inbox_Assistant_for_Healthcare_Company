package com.smartinbox.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.smartinbox.model.ReviewActionType;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "REVIEW_ACTIONS")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ReviewAction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "message_id", nullable = false)
    @JsonIgnore
    private Message message;

    @Column(name = "reviewer_name", nullable = false, length = 100)
    private String reviewerName;

    @Enumerated(EnumType.STRING)
    @Column(name = "action", nullable = false, length = 30)
    private ReviewActionType action;

    @Column(name = "target_ref", length = 255)
    private String targetRef;

    @Lob
    @Column(name = "previous_value")
    private String previousValue;

    @Lob
    @Column(name = "new_value")
    private String newValue;

    @CreationTimestamp
    @Column(name = "timestamp", nullable = false, updatable = false)
    private LocalDateTime timestamp;
}
