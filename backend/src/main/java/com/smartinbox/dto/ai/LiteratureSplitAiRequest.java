package com.smartinbox.dto.ai;

import lombok.*;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class LiteratureSplitAiRequest {
    private String articleText;
    private String filename;
    private List<Object> tables;
}
