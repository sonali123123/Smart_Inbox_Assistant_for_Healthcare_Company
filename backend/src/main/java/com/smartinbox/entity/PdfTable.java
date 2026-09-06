package com.smartinbox.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "PDF_TABLES")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PdfTable {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "attachment_id", nullable = false)
    @JsonIgnore
    private Attachment attachment;

    @Column(name = "page_number")
    private Integer pageNumber;

    @Lob
    @Column(name = "table_json", nullable = false)
    private String tableJson;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
