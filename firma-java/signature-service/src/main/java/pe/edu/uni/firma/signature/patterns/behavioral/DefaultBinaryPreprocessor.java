package pe.edu.uni.firma.signature.patterns.behavioral;

import org.springframework.core.annotation.Order;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import pe.edu.uni.firma.signature.dto.CitizenPrivateDto;

@Component
@Order(100)
public class DefaultBinaryPreprocessor implements DocumentPreprocessor {
    @Override
    public boolean supports(String fileName, String contentType) {
        return true;
    }

    @Override
    public PreparedDocument prepare(String fileName, String contentType, byte[] content, CitizenPrivateDto signer) {
        String resolvedContentType = contentType == null || contentType.isBlank()
                ? MediaType.APPLICATION_OCTET_STREAM_VALUE
                : contentType;
        return new PreparedDocument(fileName, resolvedContentType, content, false);
    }
}
