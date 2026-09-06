package com.smartinbox.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AttachmentDto {
    private Long id;
    private String filename;
    private String contentType;
    @JsonProperty("isPdf")
    private boolean isPdf;
    private String pdfType;
    private boolean loggedOnly;
    private PdfSummaryDto summary;
    private List<PdfTableDto> tables;
    private List<PdfImageDto> images;
    private PdfTranslationDto translation;

    @JsonProperty("pdf")
    public boolean getPdf() {
        return isPdf;
    }
}
