package pe.edu.uni.firma.signature.patterns.behavioral;

import java.util.List;
import org.springframework.stereotype.Component;
import pe.edu.uni.firma.signature.dto.CitizenPrivateDto;

/** Patrón Chain/Registry: selecciona la estrategia de preparación documental. */
@Component
public class DocumentPreprocessorRegistry {
    private final List<DocumentPreprocessor> preprocessors;

    public DocumentPreprocessorRegistry(List<DocumentPreprocessor> preprocessors) {
        this.preprocessors = preprocessors;
    }

    public PreparedDocument prepare(String fileName, String contentType, byte[] content, CitizenPrivateDto signer) {
        return preprocessors.stream()
                .filter(p -> p.supports(fileName, contentType))
                .findFirst()
                .orElseThrow(() -> new IllegalStateException("No existe preprocesador documental"))
                .prepare(fileName, contentType, content, signer);
    }
}
