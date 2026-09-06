package com.smartinbox.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ReviewRequest {
    private String action; // ACCEPT | OVERRIDE
    private String newCategory; // optional new Category name if OVERRIDE
    private String reviewerName;
}
