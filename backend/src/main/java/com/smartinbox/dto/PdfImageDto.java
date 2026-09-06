package com.smartinbox.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PdfImageDto {
    private Long id;
    private Integer pageNumber;
    private String description;
    private boolean reviewFlag;
}
