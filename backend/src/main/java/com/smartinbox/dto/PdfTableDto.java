package com.smartinbox.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PdfTableDto {
    private Long id;
    private Integer pageNumber;
    private String tableJson;
}
