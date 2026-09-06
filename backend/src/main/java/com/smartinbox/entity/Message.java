package com.smartinbox.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.smartinbox.model.SourceType;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;

@Entity
@Table(name = "MESSAGES")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Message {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Enumerated(EnumType.STRING)
    @Column(name = "source_type", nullable = false, length = 20)
    @Builder.Default
    private SourceType sourceType = SourceType.EMAIL;

    @Column(name = "sender", length = 255)
    private String sender;

    @Column(name = "subject", length = 500)
    private String subject;

    @Column(name = "received_date")
    private LocalDateTime receivedDate;

    @Lob
    @Column(name = "body_text")
    private String bodyText;

    @Column(name = "message_id_header", length = 500, unique = true)
    private String messageIdHeader;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @OneToMany(mappedBy = "message", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private Set<Attachment> attachments = new HashSet<>();

    @OneToMany(mappedBy = "message", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private Set<Classification> classifications = new HashSet<>();

    @OneToMany(mappedBy = "message", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private Set<ExtractedField> extractedFields = new HashSet<>();
}
