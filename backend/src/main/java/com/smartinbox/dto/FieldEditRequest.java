package com.smartinbox.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class FieldEditRequest {
    private String action; // EDIT
    private String newValue;
    private String reviewerName;
    private String reason;
}
