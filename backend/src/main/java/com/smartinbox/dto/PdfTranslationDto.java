package com.smartinbox.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PdfTranslationDto {
    private Long id;
    private String sourceLanguage;
    private String originalTextRef;
    private String translatedText;
}
