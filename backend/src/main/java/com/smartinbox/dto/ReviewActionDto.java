package com.smartinbox.dto;

import lombok.*;
import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ReviewActionDto {
    private Long id;
    private String reviewerName;
    private String action;
    private String targetRef;
    private String previousValue;
    private String newValue;
    private LocalDateTime timestamp;
}
