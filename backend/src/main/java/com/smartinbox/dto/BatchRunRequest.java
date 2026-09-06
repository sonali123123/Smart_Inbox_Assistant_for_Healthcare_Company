package com.smartinbox.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class BatchRunRequest {

    @JsonProperty("sourceDir")
    private String sourceDir;

    @JsonProperty("directoryPath")
    private String directoryPath;

    public String getSourceDir() {
        if (sourceDir != null && !sourceDir.isBlank()) {
            return sourceDir;
        }
        if (directoryPath != null && !directoryPath.isBlank()) {
            return directoryPath;
        }
        return null;
    }

    public String getEffectiveSourceDir() {
        String dir = getSourceDir();
        return (dir != null && !dir.isBlank()) ? dir : "test-data/emails";
    }
}
